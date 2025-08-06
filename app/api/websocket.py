from datetime import datetime
from typing import Dict, List

from fastapi import Query, WebSocket, WebSocketDisconnect, status

from app.db.database import (
    check_workflow_belongs_to_user,
    get_full_workflow_status_join,
    verify_auth_token,
)


def convert_datetime_to_str(obj):
    """
    dict, list, datetime 객체를 재귀적으로 순회하며
    datetime 타입은 ISO 형식 문자열로 변환.

    Args:
        obj: dict, list, datetime, 또는 기타 객체

    Returns:
        datetime이 문자열로 변환된 동일 구조의 객체
    """
    if isinstance(obj, dict):
        return {k: convert_datetime_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_str(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


class ConnectionManager:
    """
    workflow_id 별로 WebSocket 연결을 관리.
    연결 추가, 제거, 그리고 특정 workflow에 연결된
    모든 클라이언트에 메시지를 방송하는 기능을 제공.
    """

    def __init__(self):
        """
        활성 연결을 저장할 빈 딕셔너리를 초기화합니다.
        """
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, workflow_id: str, websocket: WebSocket):
        """
        새로운 WebSocket 연결을 수락하고
        해당 workflow의 초기 상태를 클라이언트에 전송.

        Args:
            workflow_id: 워크플로우 식별자
            websocket: WebSocket 연결 객체
        """
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
        """
        WebSocket 연결을 연결 목록에서 제거합니다.

        Args:
            workflow_id: 워크플로우 식별자
            websocket: 제거할 WebSocket 객체
        """
        if workflow_id in self.active_connections:
            self.active_connections[workflow_id].remove(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]

    async def broadcast(self, workflow_id: str, message: dict):
        """
        특정 workflow에 연결된 모든 WebSocket 클라이언트에게
        JSON 메시지를 전송합니다. 한 사용자가 여러 기기를 사용해 동일한 workflow에 연결을 시도할 경우를 고려하였습니다.

        Args:
            workflow_id: 워크플로우 식별자
            message: JSON 직렬화 가능한 메시지 딕셔너리
        """
        if workflow_id in self.active_connections:
            for connection in self.active_connections[workflow_id]:
                await connection.send_json(message)


manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    workflow_id: str,
    auth_token: str = Query(...),  # auth_token 쿼리 파라미터 필수
):
    """
    WebSocket 엔드포인트 처리 함수입니다.
    - auth_token을 검증하여 사용자 권한 확인
    - 권한이 없으면 연결 종료
    - 권한이 있으면 연결 수락 및 유지
    - 연결 종료 시 연결 해제 처리

    Args:
        websocket: WebSocket 연결 객체
        workflow_id: URL 경로의 워크플로우 ID
        auth_token: 쿼리 파라미터로 전달된 인증 토큰
    """
    # 1) 토큰 검증 -> user_id 반환 또는 None
    user_id = await verify_auth_token(auth_token)
    if not user_id:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION
        )  # 4008: Policy Violation
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
    """
    워크플로우 상태 변경 시, 해당 workflow에 연결된
    모든 WebSocket 클라이언트에 업데이트 내용을 방송.

    Args:
        workflow_id: 워크플로우 식별자
    """
    latest_status = await get_full_workflow_status_join(workflow_id)
    latest_status = convert_datetime_to_str(latest_status)
    await manager.broadcast(workflow_id, {"type": "update", "data": latest_status})
