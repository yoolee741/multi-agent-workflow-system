import json
from datetime import datetime, timezone
import logging
import asyncpg


async def save_agent_response(
    conn: asyncpg.Connection,
    table_name: str,
    workflow_id: str,
    status: str,
    response: dict | str,
) -> None:
    """
    agent 결과를 DB에 저장하는 함수.
    - response는 dict면 JSON으로 변환 후 저장, 아니면 문자열 그대로 저장
    - status: 'pending', 'running', 'completed', 'failed' 중 하나
    """

    if isinstance(response, dict):
        response_data = json.dumps(response)  # response 타입이 dict이면 json으로 변환
    else:
        response_data = str(response)

    now = datetime.now(timezone.utc)

    try:
        await conn.execute(
            f"""
            UPDATE {table_name}
            SET status = $1,
                response = $2,
                ended_at = $3
            WHERE workflow_id = $4
            """,
            status,
            response_data,
            now,
            workflow_id,
        )
    except Exception as e:
        logging.error(f"save_agent_response 실패: {e}")
        raise
