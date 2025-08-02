import os
import json
from pathlib import Path
from openai import OpenAI
from app.agents.base import BaseAgent

class DataCollectorAgent(BaseAgent):
    async def run(self):
        try:
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

            # TODO: 파일 저장 대신 DB에 저장
            # await save_agent_response(db, self.agent_id, response_text)

            # TODO: DB 저장시 아래 로직 제거
            output_file = self.output_path / "japan_trip_plan.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(response_text, encoding="utf-8")

            self.logger.info(f"DataCollectorAgent: saved output to {output_file}")

        except Exception as e:
            self.logger.error(f"DataCollectorAgent run error: {e}")
            # TODO: 워크플로우/agent 상태 업데이트 등 추가 처리
