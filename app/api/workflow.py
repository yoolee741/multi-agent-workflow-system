import asyncio
import uuid
from datetime import datetime, timezone

from app.agents.budget_manager import BudgetManagerAgent
from app.agents.data_collector import DataCollectorAgent
from app.agents.itinerary_builder import ItineraryBuilderAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.db.database import connect_db


async def _run_agents_in_background(workflow_id: str) -> list | None:
    """
    주어진 workflow_id로 여러 Agent를 순차 및 병렬로 실행하는 비동기 함수.

    실행 순서:
    1) DataCollectorAgent 실행 (실패 시 이후 단계 실행 안 함)
    2) BudgetManagerAgent와 ItineraryBuilderAgent 병렬 실행
    3) ReportGeneratorAgent 실행

    각 Agent 실행 결과(성공, 실패, 결과 메시지 등)를 리스트에 저장.

    Args:
        workflow_id (str): 실행할 워크플로우의 고유 ID

    Returns:
        list[dict] | None: 각 Agent 실행 결과 리스트 혹은 DataCollectorAgent 실패 시 None 반환

    예외:
        내부에서 예외를 처리하며, 호출자에게는 예외를 전달X.
    """
    results = []

    dc_agent = DataCollectorAgent(workflow_id)
    try:
        dc_result = await dc_agent.run()
        results.append(
            {"agent": "DataCollectorAgent", "status": "success", "result": dc_result}
        )
    except Exception as e:
        results.append(
            {"agent": "DataCollectorAgent", "status": "error", "error": str(e)}
        )
        # 실패 시 이후 단계 건너뛰기
        return

    bm_agent = BudgetManagerAgent(workflow_id)
    ib_agent = ItineraryBuilderAgent(workflow_id)
    agent_tasks = [bm_agent.run(), ib_agent.run()]
    parallel_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

    for agent, res in zip([bm_agent, ib_agent], parallel_results):
        if isinstance(res, Exception):
            results.append(
                {
                    "agent": agent.__class__.__name__,
                    "status": "error",
                    "error": str(res),
                }
            )
        else:
            results.append(
                {"agent": agent.__class__.__name__, "status": "success", "result": res}
            )

    rg_agent = ReportGeneratorAgent(workflow_id)
    try:
        rg_result = await rg_agent.run()
        results.append(
            {"agent": "ReportGeneratorAgent", "status": "success", "result": rg_result}
        )
    except Exception as e:
        results.append(
            {"agent": "ReportGeneratorAgent", "status": "error", "error": str(e)}
        )


async def run_workflow(user_name: str):
    pool = await connect_db()

    async with pool.acquire() as conn:
        async with conn.transaction():
            user = await conn.fetchrow(
                "SELECT user_id FROM users WHERE name = $1", user_name
            )
            if not user:
                raise ValueError(f"User '{user_name}' not found")
            user_id = user["user_id"]

            workflow_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO workflow (workflow_id, user_id, started_at) VALUES ($1, $2, $3)",
                workflow_id,
                user_id,
                datetime.now(timezone.utc),
            )

            agents = [
                "data_collector",
                "itinerary_builder",
                "budget_manager",
                "report_generator",
            ]
            for agent in agents:
                await conn.execute(
                    f"INSERT INTO {agent} (workflow_id) VALUES ($1)", workflow_id
                )

    # 백그라운드에서 에이전트 실행 시작 (비동기 태스크로 띄움)
    asyncio.create_task(_run_agents_in_background(workflow_id))

    # 바로 workflow_id만 반환
    return {"workflow_id": workflow_id}
