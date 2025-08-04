import asyncpg
from typing import AsyncGenerator
from fastapi import Depends
import os
from dotenv import load_dotenv

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

# 단순 커넥션 반환 함수 (에이전트 코드에서 직접 사용)

async def get_single_connection() -> asyncpg.Connection:
    pool = await connect_db()
    return await pool.acquire()
