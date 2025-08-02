# # Rest API
# # 워크플로우 시작 api

# from app.agents.budget_manager import BudgetManagerAgent
# from app.agents.data_collector import DataCollectorAgent
# from app.agents.itinerary_builder import ItineraryBuilderAgent
# from pathlib import Path

# async def run_workflow(workflow_id: str, input_path: str, output_path: str):
#     agents = [
#         BudgetManagerAgent(workflow_id, Path(input_path), Path(output_path)),
#         DataCollectorAgent(workflow_id, Path(input_path), Path(output_path)),
#         ItineraryBuilderAgent(workflow_id, Path(input_path), Path(output_path)),
#     ]
#     results = []
#     for agent in agents:
#         try:
#             result = await agent.run()
#             results.append({
#                 "agent": agent.__class__.__name__,
#                 "status": "success",
#                 "result": result
#             })
#         except Exception as e:
#             results.append({
#                 "agent": agent.__class__.__name__,
#                 "status": "error",
#                 "error": str(e)
#             })
#     return results


# # WebSocket API

import asyncio
from app.agents.data_collector import DataCollectorAgent
from app.agents.budget_manager import BudgetManagerAgent
from app.agents.itinerary_builder import ItineraryBuilderAgent
from pathlib import Path

async def run_workflow(workflow_id: str, input_path: str, output_path: str):
    # 1단계: DataCollectorAgent 먼저 단독 실행 (이게 끝나야 이후 병렬 실행 가능)
    dc_agent = DataCollectorAgent(workflow_id, Path(input_path), Path(output_path))
    try:
        dc_result = await dc_agent.run()
    except Exception as e:
        return [{"agent": "DataCollectorAgent", "status": "error", "error": str(e)}]
    
    # 2단계: BudgetManagerAgent, ItineraryBuilderAgent를 동시에 실행
    bm_agent = BudgetManagerAgent(workflow_id, Path(input_path), Path(output_path))
    ib_agent = ItineraryBuilderAgent(workflow_id, Path(input_path), Path(output_path))
    results = []
    agent_tasks = [
        bm_agent.run(),
        ib_agent.run(),
    ]
    parallel_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
    
    # 결과 정리
    for agent, res in zip([bm_agent, ib_agent], parallel_results):
        if isinstance(res, Exception):
            results.append({
                "agent": agent.__class__.__name__,
                "status": "error",
                "error": str(res)
            })
        else:
            results.append({
                "agent": agent.__class__.__name__,
                "status": "success",
                "result": res
            })
    # DataCollectorAgent 결과 포함
    results.insert(0, {
        "agent": dc_agent.__class__.__name__,
        "status": "success",
        "result": dc_result
    })
    return results

