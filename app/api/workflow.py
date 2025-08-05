import asyncio
import uuid
from app.agents.data_collector import DataCollectorAgent
from app.agents.budget_manager import BudgetManagerAgent
from app.agents.itinerary_builder import ItineraryBuilderAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.db.database import connect_db
from datetime import datetime

async def _run_agents_in_background(workflow_id: str):
    results = []

    dc_agent = DataCollectorAgent(workflow_id)
    try:
        dc_result = await dc_agent.run()
        results.append({"agent": "DataCollectorAgent", "status": "success", "result": dc_result})
    except Exception as e:
        results.append({"agent": "DataCollectorAgent", "status": "error", "error": str(e)})
        # 실패 시 이후 단계 건너뛰기
        return

    bm_agent = BudgetManagerAgent(workflow_id)
    ib_agent = ItineraryBuilderAgent(workflow_id)
    agent_tasks = [bm_agent.run(), ib_agent.run()]
    parallel_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

    for agent, res in zip([bm_agent, ib_agent], parallel_results):
        if isinstance(res, Exception):
            results.append({"agent": agent.__class__.__name__, "status": "error", "error": str(res)})
        else:
            results.append({"agent": agent.__class__.__name__, "status": "success", "result": res})

    rg_agent = ReportGeneratorAgent(workflow_id)
    try:
        rg_result = await rg_agent.run()
        results.append({"agent": "ReportGeneratorAgent", "status": "success", "result": rg_result})
    except Exception as e:
        results.append({"agent": "ReportGeneratorAgent", "status": "error", "error": str(e)})


async def run_workflow(user_name: str):
    pool = await connect_db()

    async with pool.acquire() as conn:
        async with conn.transaction():
            user = await conn.fetchrow("SELECT user_id FROM users WHERE name = $1", user_name)
            if not user:
                raise ValueError(f"User '{user_name}' not found")
            user_id = user["user_id"]

            workflow_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO workflow (workflow_id, user_id, started_at) VALUES ($1, $2, $3)",
                workflow_id, user_id, datetime.utcnow()
            )

            agents = ["data_collector", "itinerary_builder", "budget_manager", "report_generator"]
            for agent in agents:
                await conn.execute(
                    f"INSERT INTO {agent} (workflow_id) VALUES ($1)",
                    workflow_id
                )

    # 백그라운드에서 에이전트 실행 시작 (비동기 태스크로 띄움)
    asyncio.create_task(_run_agents_in_background(workflow_id))

    # 바로 workflow_id만 반환
    return {"workflow_id": workflow_id}