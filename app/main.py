import asyncio
import logging
from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    **  @app.on_event("startup") -> deprecated
    * 애플리케이션 시작 전, 후에 실행되어야 하는 로직(코드)을 정의
    * 전체 애플리케이션에서 사용해야 하는 자원을 설정하거나 요청 간에 공유되는 자원을 설정하고, 또는 그 후에 정리하는 데 유용

    """
    retries = 10
    delay = 3
    for i in range(retries):
        try:
            pool = await connect_db()
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            app.state.db_pool = pool  # FastAPI 애플리케이션 인스턴스(app)의 상태 저장 공간에 커넥션 풀 객체를 저장 -> 앱이 살아있는 동안 커넥션 풀을 안전하게 공유
            logging.info("DB 연결 성공")
            break
        except Exception as e:
            logging.warning(f"DB 연결 실패 {i + 1}/{retries}, 재시도 중... {e}")
            await asyncio.sleep(delay)
    else:
        logging.error("DB 연결 실패 - 서버 시작 중단")
        raise RuntimeError("DB 연결 실패 - 서버 시작 중단")

    yield  # 서버 실행

    # 서버 종료 시 실행되는 코드
    logging.info("서버 종료: 커넥션 풀 닫는 중...")
    await app.state.db_pool.close()
    logging.info("커넥션 풀 닫힘 완료")


app = FastAPI(lifespan=lifespan)


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
