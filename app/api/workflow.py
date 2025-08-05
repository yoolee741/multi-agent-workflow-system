import asyncio
import uuid
from app.agents.data_collector import DataCollectorAgent
from app.agents.budget_manager import BudgetManagerAgent
from app.agents.itinerary_builder import ItineraryBuilderAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.db.database import connect_db
from datetime import datetime

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

    results = []
    # 1단계: DataCollectorAgent 먼저 단독 실행 (이게 끝나야 이후 병렬 실행 가능)
    dc_agent = DataCollectorAgent(workflow_id)
    try:
        dc_result = await dc_agent.run()
        results.append({"agent": "DataCollectorAgent", "status": "success", "result": dc_result})
    except Exception as e:
        results.append({"agent": "DataCollectorAgent", "status": "error", "error": str(e)})
        return {"workflow_id": workflow_id, "results": results}

    # 2단계: BudgetManagerAgent, ItineraryBuilderAgent를 동시에 실행
    bm_agent = BudgetManagerAgent(workflow_id)
    ib_agent = ItineraryBuilderAgent(workflow_id)
    agent_tasks = [bm_agent.run(), ib_agent.run()]
    parallel_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

    for agent, res in zip([bm_agent, ib_agent], parallel_results):
        if isinstance(res, Exception):
            results.append({"agent": agent.__class__.__name__, "status": "error", "error": str(res)})
        else:
            results.append({"agent": agent.__class__.__name__, "status": "success", "result": res})

    # 3단계: ReportGeneratorAgent 단독 실행
    rg_agent = ReportGeneratorAgent(workflow_id)
    try:
        rg_result = await rg_agent.run()
        results.append({"agent": "ReportGeneratorAgent", "status": "success", "result": rg_result})
    except Exception as e:
        results.append({"agent": "ReportGeneratorAgent", "status": "error", "error": str(e)})

    return {"workflow_id": workflow_id, "results": results}
