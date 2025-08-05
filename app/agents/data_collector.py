import os
import json
from pathlib import Path
from openai import OpenAI
from app.agents.base import BaseAgent
from datetime import datetime
from app.db.utils import save_agent_response
from app.db.database import connect_db

class DataCollectorAgent(BaseAgent):
    async def run(self):
        pool = await connect_db()
        async with pool.acquire() as conn:
            try:
                # 작업 시작 시 status = running, started_at 갱신
                await conn.execute(
                    "UPDATE data_collector SET status = 'running', started_at = $1 WHERE workflow_id = $2",
                    datetime.utcnow(), self.workflow_id
                )

                client = OpenAI(
                    base_url="https://api.deepauto.ai/openai/v1",
                    api_key=os.getenv("API_KEY"),
                )

                system_prompt = "You are the Data Collector agent."
                user_prompt = """
You are the Data Collector agent.

Input:

total_budget: 3000 USD

preferred_route: ["Tokyo", "Kyoto", "Osaka"]

accommodation_type: "3-star hotel"

travel_dates:

start_date: "2025-10-01"

end_date: "2025-10-05"

special_interests: ["onsen", "local cuisine", "temple visits"]

Task:

1. Using the fixed input above, fetch via APIs or web scraping:
    - Round-trip flights (ICN ⇄ NRT/KIX)
    - 3-star hotels in each city
    - JR Pass cost and regional transfers
    - Major attraction hours, public holidays, and festival dates
    - 5-day weather forecasts for Tokyo, Kyoto, Osaka
2. Aggregate into JSON:

{
"preferences": { …fixed… },
"flights": [ … ],
"hotels": [ … ],
"transport": { … },
"attractions": [ … ],
"weather": [ … ]
}

IMPORTANT:
- **Your response MUST be ONLY a valid JSON object.**
- **Do NOT include any explanations, markdown, or code blocks.**
- **Just output a single, valid JSON object, and nothing else.**

3. Show all the steps and the reasoning process.
4. Save this JSON to a file named japan_trip_plan.json.
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

                # DB에 저장
                await save_agent_response(conn, "data_collector", self.workflow_id, "completed", response_text)

                self.logger.info(f"DataCollectorAgent: saved output to DB for workflow {self.workflow_id}")

                return response_text

            except Exception as e:
                self.logger.error(f"DataCollectorAgent run error: {e}")
                error_response = {"error": str(e)}
                # 실패 시 status = failed, 에러 메시지 저장
                await save_agent_response(conn, "data_collector", self.workflow_id, "failed", error_response)
                # 워크플로우 상태도 failed로 업데이트
                await conn.execute(
                    "UPDATE workflow SET status = 'failed' WHERE workflow_id = $1",
                    self.workflow_id
                )                
                raise e
