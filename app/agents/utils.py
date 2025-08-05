async def check_agent_status(conn, agent_table: str, workflow_id: str) -> str | None:
    """
    특정 agent의 상태를 체크해서 오류 메시지를 반환하거나 정상인 경우 None을 반환.

    - conn: DB 커넥션
    - agent_table: 체크할 agent 테이블명 (예: "data_collector")
    - workflow_id: 워크플로우 ID
    

    반환값:
    - 오류 메시지(str) 또는 None (문제가 없으면)
    """
    record = await conn.fetchrow(
        f"SELECT status, response FROM {agent_table} WHERE workflow_id = $1",
        workflow_id
    )

    if not record:
        return f"{agent_table} record not found in DB"
    elif record['status'] != 'completed':
        return f"{agent_table} status is {record['status']}, not completed"
    return None
