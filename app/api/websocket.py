from fastapi import WebSocket, WebSocketDisconnect, Query, status
from typing import Dict, List
from app.db.database import verify_auth_token, check_workflow_belongs_to_user, get_full_workflow_status_join
from datetime import datetime

def convert_datetime_to_str(obj):
    if isinstance(obj, dict):
        return {k: convert_datetime_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_str(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, workflow_id: str, websocket: WebSocket):
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)

        # 연결 시 초기 상태 전송
        initial_status = await get_full_workflow_status_join(workflow_id)

        # datetime 객체를 문자열로 변환
        initial_status = convert_datetime_to_str(initial_status)

        await websocket.send_json({"type": "init", "data": initial_status})

    def disconnect(self, workflow_id: str, websocket: WebSocket):
        if workflow_id in self.active_connections:
            self.active_connections[workflow_id].remove(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]

    async def broadcast(self, workflow_id: str, message: dict):
        if workflow_id in self.active_connections:
            for connection in self.active_connections[workflow_id]:
                await connection.send_json(message)

manager = ConnectionManager()

async def websocket_endpoint(
    websocket: WebSocket,
    workflow_id: str,
    auth_token: str = Query(...),  # auth_token 쿼리 파라미터 필수
):
    # 1) 토큰 검증 -> user_id 반환 또는 None
    user_id = await verify_auth_token(auth_token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)  # 4008: Policy Violation
        return

    # 2) 권한 체크: workflow_id가 user_id 소유인지 확인
    allowed = await check_workflow_belongs_to_user(workflow_id, user_id)
    if not allowed:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)  # 권한 없으면 종료
        return

    # 3) 연결 허용 및 WebSocket 관리
    await manager.connect(workflow_id, websocket)

    try:
        while True:
            # 클라이언트 메시지 수신(필요 시 처리)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(workflow_id, websocket)

# WebSocket 상태 변경 알림용 함수
async def notify_workflow_update(workflow_id: str):
    latest_status = await get_full_workflow_status_join(workflow_id)
    latest_status = convert_datetime_to_str(latest_status)
    await manager.broadcast(workflow_id, {"type": "update", "data": latest_status})
