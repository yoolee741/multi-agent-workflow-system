import os
import uuid

import asyncpg
import asyncio
from dotenv import load_dotenv

load_dotenv()  # .env 파일 읽기

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None  # 전역 변수


async def connect_db(retries=5, delay=2):
    """
    데이터베이스 연결 풀 생성 및 반환.
    연결 실패 시 재시도.

    Args:
        retries (int): 재시도 횟수 (기본 5)
        delay (int): 재시도 간 대기 시간 (초, 기본 2초)

    Returns:
        asyncpg.Pool: DB 연결 풀 객체
    """
    global _pool
    if _pool is None:
        for attempt in range(retries):
            try:
                _pool = await asyncpg.create_pool(DATABASE_URL)
                return _pool
            except Exception as e:
                if attempt == retries - 1:
                    raise
                print(f"DB 연결 실패, 재시도 {attempt + 1}/{retries}... {e}")
                await asyncio.sleep(delay)
    else:
        return _pool


async def get_full_workflow_status_join(workflow_id: str):
    """
    주어진 workflow_id에 대해 workflow 및 관련 agent들의 상태와 결과를 조인하여 조회.

    Args:
        workflow_id (str): 조회할 워크플로우 ID

    Returns:
        dict | None: workflow 기본 정보와 각 agent별 상태 및 결과를 포함하는 딕셔너리,
                     workflow가 없으면 None 반환
    """
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
              w.*,
              dc.data_collector_id AS dc_id,
              dc.status AS dc_status,
              dc.response AS dc_response,
              dc.started_at AS dc_started_at,
              dc.ended_at AS dc_ended_at,

              ib.itinerary_builder_id AS ib_id,
              ib.status AS ib_status,
              ib.response AS ib_response,
              ib.started_at AS ib_started_at,
              ib.ended_at AS ib_ended_at,

              bm.budget_manager_id AS bm_id,
              bm.status AS bm_status,
              bm.response AS bm_response,
              bm.started_at AS bm_started_at,
              bm.ended_at AS bm_ended_at,

              rg.report_generator_id AS rg_id,
              rg.status AS rg_status,
              rg.response AS rg_response,
              rg.started_at AS rg_started_at,
              rg.ended_at AS rg_ended_at

            FROM workflow w
            LEFT JOIN data_collector dc ON w.workflow_id = dc.workflow_id
            LEFT JOIN itinerary_builder ib ON w.workflow_id = ib.workflow_id
            LEFT JOIN budget_manager bm ON w.workflow_id = bm.workflow_id
            LEFT JOIN report_generator rg ON w.workflow_id = rg.workflow_id
            WHERE w.workflow_id = $1
            """,
            workflow_id,
        )

        if not row:
            return None

        workflow_data = {
            k: row[k]
            for k in row.keys()
            if not k.startswith(("dc_", "ib_", "bm_", "rg_"))
        }

        # UUID 필드들 문자열로 변환
        for k, v in workflow_data.items():
            if isinstance(v, uuid.UUID):
                workflow_data[k] = str(v)

        agents = {
            "data_collector": {
                "id": str(row["dc_id"]) if row["dc_id"] else None,
                "status": row["dc_status"],
                "response": row["dc_response"],
                "started_at": (
                    str(row["dc_started_at"]) if row["dc_started_at"] else None
                ),
                "ended_at": str(row["dc_ended_at"]) if row["dc_ended_at"] else None,
            },
            "itinerary_builder": {
                "id": str(row["ib_id"]) if row["ib_id"] else None,
                "status": row["ib_status"],
                "response": row["ib_response"],
                "started_at": (
                    str(row["ib_started_at"]) if row["ib_started_at"] else None
                ),
                "ended_at": str(row["ib_ended_at"]) if row["ib_ended_at"] else None,
            },
            "budget_manager": {
                "id": str(row["bm_id"]) if row["bm_id"] else None,
                "status": row["bm_status"],
                "response": row["bm_response"],
                "started_at": (
                    str(row["bm_started_at"]) if row["bm_started_at"] else None
                ),
                "ended_at": str(row["bm_ended_at"]) if row["bm_ended_at"] else None,
            },
            "report_generator": {
                "id": str(row["rg_id"]) if row["rg_id"] else None,
                "status": row["rg_status"],
                "response": row["rg_response"],
                "started_at": (
                    str(row["rg_started_at"]) if row["rg_started_at"] else None
                ),
                "ended_at": str(row["rg_ended_at"]) if row["rg_ended_at"] else None,
            },
        }

        return {
            "workflow": workflow_data,
            "agents": agents,
        }


async def verify_auth_token(token: str) -> int | None:
    """
    인증 토큰을 검증하여 해당 토큰이 유효한 경우 user_id를 반환.

    Args:
        token (str): 인증 토큰 문자열

    Returns:
        int | None: 유효한 토큰인 경우 user_id 반환, 그렇지 않으면 None 반환
    """
    pool = await connect_db()  # connect_db()가 _pool 초기화도 담당
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id FROM users WHERE auth_token = $1", token
        )
        if row:
            return row["user_id"]
        return None


async def check_workflow_belongs_to_user(workflow_id: str, user_id: int) -> bool:
    """
    주어진 workflow_id가 해당 user_id 소유인지 확인.

    Args:
        workflow_id (str): 워크플로우 고유 ID
        user_id (int): 사용자 ID

    Returns:
        bool: 소유주이면 True, 아니면 False
    """
    pool = await connect_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM workflow WHERE workflow_id = $1 AND user_id = $2",
            workflow_id,
            user_id,
        )
        return row is not None
