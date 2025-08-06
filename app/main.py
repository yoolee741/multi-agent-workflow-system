import asyncio
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Query, WebSocket
from pydantic import BaseModel

from app.api.websocket import websocket_endpoint
from app.api.workflow import run_workflow
from app.db.database import connect_db

load_dotenv()

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,  # INFO 이상 로그 출력
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)


@app.on_event("startup")
async def startup_event():
    retries = 10
    delay = 3
    for i in range(retries):
        try:
            pool = await connect_db()
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            print("DB 연결 성공")
            return
        except Exception as e:
            print(f"DB 연결 실패 {i+1}/{retries}, 재시도 중... {e}")
            await asyncio.sleep(delay)
    raise RuntimeError("DB 연결 실패 - 서버 시작 중단")


class WorkflowRequest(BaseModel):
    user_name: str


@app.post("/workflow/start")
async def start_workflow(req: WorkflowRequest):
    result = await run_workflow(
        req.user_name,
    )
    return {"workflow_id": result["workflow_id"]}


@app.get("/")
def root():
    return {"msg": "Multi-Agent Workflow API is running!"}


@app.websocket("/ws/{workflow_id}")
async def websocket_route(
    websocket: WebSocket,
    workflow_id: str,
    auth_token: str = Query(...),
):
    await websocket_endpoint(websocket, workflow_id, auth_token)
