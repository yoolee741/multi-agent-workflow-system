async def save_agent_response(
    conn, table_name: str, workflow_id: str, status: str, response: dict | str
):
    """
    agent 결과를 DB에 저장하는 함수.
    - response는 dict면 JSON으로 변환 후 저장, 아니면 문자열 그대로 저장
    - status: 'pending', 'running', 'completed', 'failed' 중 하나
    """
    import json

    if isinstance(response, dict):
        response_data = json.dumps(response)
    else:
        response_data = str(response)

    # started_at, ended_at은 현재 시간으로 자동 처리 가능하지만,
    # 필요한 경우 별도로 인자로 받을 수도 있음
    from datetime import datetime

    now = datetime.utcnow()

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
