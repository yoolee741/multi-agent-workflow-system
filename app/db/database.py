import asyncpg
from typing import AsyncGenerator
from fastapi import Depends
import os
from dotenv import load_dotenv
import uuid


load_dotenv()  # .env 파일 읽기

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None

async def connect_db():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool

async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = await connect_db()
    async with pool.acquire() as connection:
        yield connection

async def get_full_workflow_status_join(workflow_id: str):
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
            workflow_id
        )

        if not row:
            return None

        workflow_data = {k: row[k] for k in row.keys() if not k.startswith(("dc_", "ib_", "bm_", "rg_"))}

        # UUID 필드들 문자열로 변환 
        for k, v in workflow_data.items():
            if isinstance(v, uuid.UUID):
                workflow_data[k] = str(v)

        agents = {
            "data_collector": {
                "id": str(row["dc_id"]) if row["dc_id"] else None,
                "status": row["dc_status"],
                "response": row["dc_response"],
                "started_at": str(row["dc_started_at"]) if row["dc_started_at"] else None,
                "ended_at": str(row["dc_ended_at"]) if row["dc_ended_at"] else None,
            },
            "itinerary_builder": {
                "id": str(row["ib_id"]) if row["ib_id"] else None,
                "status": row["ib_status"],
                "response": row["ib_response"],
                "started_at": str(row["ib_started_at"]) if row["ib_started_at"] else None,
                "ended_at": str(row["ib_ended_at"]) if row["ib_ended_at"] else None,
            },
            "budget_manager": {
                "id": str(row["bm_id"]) if row["bm_id"] else None,
                "status": row["bm_status"],
                "response": row["bm_response"],
                "started_at": str(row["bm_started_at"]) if row["bm_started_at"] else None,
                "ended_at": str(row["bm_ended_at"]) if row["bm_ended_at"] else None,
            },
            "report_generator": {
                "id": str(row["rg_id"]) if row["rg_id"] else None,
                "status": row["rg_status"],
                "response": row["rg_response"],
                "started_at": str(row["rg_started_at"]) if row["rg_started_at"] else None,
                "ended_at": str(row["rg_ended_at"]) if row["rg_ended_at"] else None,
            },
        }

        return {
            "workflow": workflow_data,
            "agents": agents,
        }

async def verify_auth_token(token: str) -> int | None:
    pool = await connect_db()  # connect_db()가 _pool 초기화도 담당
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT user_id FROM users WHERE auth_token = $1", token)
        if row:
            return row["user_id"]
        return None


async def check_workflow_belongs_to_user(workflow_id: str, user_id: int) -> bool:
    pool = await connect_db()  
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT 1 FROM workflow WHERE workflow_id = $1 AND user_id = $2", workflow_id, user_id)
        return row is not None
