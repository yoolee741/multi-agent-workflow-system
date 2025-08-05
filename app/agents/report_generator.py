import os
import json
from pathlib import Path
from openai import OpenAI
from app.agents.base import BaseAgent
from datetime import datetime
from app.db.utils import save_agent_response
from app.db.database import connect_db
from app.agents.utils import check_agent_status

class ReportGeneratorAgent(BaseAgent):
    async def run(self):
        pool = await connect_db()
        async with pool.acquire() as conn:
            try:
                # 시작 상태 업데이트
                await conn.execute(
                    "UPDATE report_generator SET status = 'running', started_at = $1 WHERE workflow_id = $2",
                    datetime.utcnow(), self.workflow_id
                )

                # ItineraryBuilder agent 상태 체크
                error_msg = await check_agent_status(conn, "itinerary_builder", self.workflow_id)
                if error_msg:
                    self.logger.error(error_msg)
                    await save_agent_response(conn, "report_generator", self.workflow_id, "failed", {"error": error_msg})
                    return

                # BudgetManager agent 상태 체크
                error_msg = await check_agent_status(conn, "budget_manager", self.workflow_id)
                if error_msg:
                    self.logger.error(error_msg)
                    await save_agent_response(conn, "report_generator", self.workflow_id, "failed", {"error": error_msg})
                    return

                # response 데이터 읽기 (여기서는 이미 존재한다고 가정)
                itinerary_record = await conn.fetchrow(
                    "SELECT response FROM itinerary_builder WHERE workflow_id = $1",
                    self.workflow_id
                )
                budget_record = await conn.fetchrow(
                    "SELECT response FROM budget_manager WHERE workflow_id = $1",
                    self.workflow_id
                )

                itinerary_json = itinerary_record['response']
                if isinstance(itinerary_json, str):
                    itinerary_data = json.loads(itinerary_json)
                else:
                    itinerary_data = itinerary_json

                budget_json = budget_record['response']
                if isinstance(budget_json, str):
                    budget_data = json.loads(budget_json)
                else:
                    budget_data = budget_json

                pretty_itinerary = json.dumps(itinerary_data, indent=2)
                pretty_budget = json.dumps(budget_data, indent=2)

                client = OpenAI(
                    base_url="https://api.deepauto.ai/openai/v1",
                    api_key=os.getenv("API_KEY"),
                )

                system_prompt = "You are the Report Generator agent."

                user_prompt = f"""
You are the Report Generator agent.

Input:

itinerary: 
{pretty_itinerary}

budget_report: 
{pretty_budget}

Task:

1. Combine the two JSONs into a single report.
2. Include sections:
    - Trip Overview (2025-10-01 to 2025-10-05, route, total_budget)
    - Day-by-Day Itinerary (with times, locations, notes)
    - Budget Summary Table (allocated/spent/remaining)
    - Reservation Checklist (flight#, hotel names, JR Pass)
    - Packing & Pre-departure Reminders
3. Highlight:
    - Cost-saving tips
    - Must-see spots
    - Onsen & temple visit recommendations

4. Show all the steps and the reasoning process.

5. Save the report to a file named report.md.
"""

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                response_text = ""

                chat_completion = client.chat.completions.create(
                    model="openai/gpt-4o-mini-2024-07-18",
                    messages=messages,
                    stream=True,
                )

                for chunk in chat_completion:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        response_text += delta.content

                # response_text를 JSON으로 감싸서 저장
                json_wrapped = json.dumps({"markdown": response_text})
                await save_agent_response(conn, "report_generator", self.workflow_id, "completed", json_wrapped)
                
                # workflow도 업데이트
                await conn.execute(
                    "UPDATE workflow SET status = 'completed' WHERE workflow_id = $1",
                    self.workflow_id
                )
                self.logger.info(f"ReportGeneratorAgent: saved output to DB for workflow {self.workflow_id}")

                return response_text

            except Exception as e:
                self.logger.error(f"ReportGeneratorAgent run error: {e}")
                error_response = {"error": str(e)}
                await save_agent_response(conn, "report_generator", self.workflow_id, "failed", error_response)
                await conn.execute(
                    "UPDATE workflow SET status = 'failed' WHERE workflow_id = $1",
                    self.workflow_id
                )
                raise e
