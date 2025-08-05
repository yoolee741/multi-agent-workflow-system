import os
import json
from pathlib import Path
from openai import OpenAI
from app.agents.base import BaseAgent
from datetime import datetime
from app.db.utils import save_agent_response  # DB 저장 함수
from app.db.database import connect_db
from app.agents.utils import check_agent_status  # 상태 체크 함수 import

class BudgetManagerAgent(BaseAgent):
    async def run(self):
        pool = await connect_db()
        async with pool.acquire() as conn:
            try:
                # 시작 상태 업데이트
                await conn.execute(
                    "UPDATE budget_manager SET status = 'running', started_at = $1 WHERE workflow_id = $2",
                    datetime.utcnow(), self.workflow_id
                )

                # data_collector agent 상태 체크
                error_msg = await check_agent_status(conn, "data_collector", self.workflow_id)
                if error_msg:
                    self.logger.error(error_msg)
                    await save_agent_response(conn, "budget_manager", self.workflow_id, "failed", {"error": error_msg})
                    return

                # DB에서 data_collector agent 결과 읽기
                record = await conn.fetchrow(
                    "SELECT response FROM data_collector WHERE workflow_id = $1",
                    self.workflow_id
                )

                trip_plan_json = record['response']
                if isinstance(trip_plan_json, str):
                    trip_plan_data = json.loads(trip_plan_json)
                else:
                    trip_plan_data = trip_plan_json

                pretty_trip_plan = json.dumps(trip_plan_data, indent=2)

                client = OpenAI(
                    base_url="https://api.deepauto.ai/openai/v1",
                    api_key=os.getenv("API_KEY"),
                )

                system_prompt = "You are the Budget Manager agent."

                user_prompt = f"""
You are the Budget Manager agent.

Input:

{pretty_trip_plan}

Task:

1. Allocate 3000 USD budget as:
    - Flights: 800 USD
    - Accommodation: 1000 USD
    - Transport (non-JR): 200 USD
    - Meals: 600 USD
    - Entrance fees: 400 USD

2. Calculate spent vs. remaining using provided prices.

3. If any category exceeds allocation, suggest cheaper alternatives like 2-star hotels or local bus.

4. Produce budget_report JSON with fields:
    {{
    "allocated": {{ ... }},
    "spent": {{ ... }},
    "remaining": {{ ... }},
    "alternatives": [ ... ]
    }}

IMPORTANT:
- **Your response MUST be ONLY a valid JSON object.**
- **Do NOT include any explanations, markdown, or code blocks.**
- **Just output a single, valid JSON object, and nothing else.**

5. Show all steps and reasoning.

6. Save this JSON to a file named budget.json.
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

                # DB에 결과 저장
                await save_agent_response(conn, "budget_manager", self.workflow_id, "completed", response_text)

                self.logger.info(f"BudgetManagerAgent: saved output to DB for workflow {self.workflow_id}")

                return response_text

            except Exception as e:
                self.logger.error(f"BudgetManagerAgent run error: {e}")
                error_response = {"error": str(e)}
                await save_agent_response(conn, "budget_manager", self.workflow_id, "failed", error_response)
                # 워크플로우 상태도 failed로 업데이트
                await conn.execute(
                    "UPDATE workflow SET status = 'failed' WHERE workflow_id = $1",
                    self.workflow_id
                )
                raise e
