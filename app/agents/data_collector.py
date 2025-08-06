import os
from datetime import datetime, timezone

from openai import OpenAI

from app.agents.base import BaseAgent
from app.api.websocket import notify_workflow_update
from app.db.database import connect_db
from app.db.utils import save_agent_response


class DataCollectorAgent(BaseAgent):
    async def run(self):
        """
        데이터 수집 에이전트의 주요 실행 메서드.

        - 에이전트 상태를 'running'으로 업데이트하고 시작 시간 기록.
        - OpenAI API를 통해 여행 데이터(항공권, 호텔, 교통, 관광지, 날씨 등) 수집 및 JSON 형태로 생성.
        - 결과를 데이터베이스에 저장하고 상태 변경을 WebSocket으로 알림.
        - 오류 발생 시 에러 상태와 메시지를 DB에 기록하고 워크플로우 상태를 실패로 업데이트하며 알림 전송.

        Returns:
            str: OpenAI로부터 생성된 JSON 응답 텍스트.

        Raises:
            Exception: 내부 예외는 로깅 후 재발생하여 호출자에게 전달.
        """
        pool = await connect_db()
        async with pool.acquire() as conn:
            try:
                # 작업 시작 시 status = running, started_at 갱신
                await conn.execute(
                    "UPDATE data_collector SET status = 'running', started_at = $1 WHERE workflow_id = $2",
                    datetime.now(timezone.utc),
                    self.workflow_id,
                )

                # 상태 변경 알림 웹소켓 푸시
                await notify_workflow_update(self.workflow_id)

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
                await save_agent_response(
                    conn, "data_collector", self.workflow_id, "completed", response_text
                )

                # 상태 변경 알림 푸시
                await notify_workflow_update(self.workflow_id)

                self.logger.info(
                    f"DataCollectorAgent: saved output to DB for workflow {self.workflow_id}"
                )

                return response_text

            except Exception as e:
                self.logger.error(f"DataCollectorAgent run error: {e}")
                error_response = {"error": str(e)}
                # 실패 시 status = failed, 에러 메시지 저장
                await save_agent_response(
                    conn, "data_collector", self.workflow_id, "failed", error_response
                )

                # 워크플로우 상태도 failed로 업데이트
                await conn.execute(
                    "UPDATE workflow SET status = 'failed' WHERE workflow_id = $1",
                    self.workflow_id,
                )

                # 상태 변경 알림 푸시
                await notify_workflow_update(self.workflow_id)
                raise e
