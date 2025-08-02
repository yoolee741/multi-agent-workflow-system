import os
import json
from pathlib import Path
from openai import OpenAI
from app.agents.base import BaseAgent

class BudgetManagerAgent(BaseAgent):
    async def run(self):
        try:
            client = OpenAI(
                base_url="https://api.deepauto.ai/openai/v1",
                api_key=os.getenv("API_KEY"),
            )

            # 이전 agent 결과 읽기 (파일에서)
            input_file = self.input_path / "japan_trip_plan.json"
            if not input_file.exists():
                self.logger.error(f"Input file not found: {input_file}")
                return

            with input_file.open("r", encoding="utf-8") as f:
                trip_plan_json = f.read()

            trip_plan_data = json.loads(trip_plan_json)
            pretty_trip_plan = json.dumps(trip_plan_data, indent=2)

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

            # TODO: 파일 저장 대신 DB에 저장
            # await save_agent_response(db, self.agent_id, response_text)

            # TODO: DB 저장시 아래 로직 제거
            output_file = self.output_path / "budget.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(response_text, encoding="utf-8")

            self.logger.info(f"BudgetManagerAgent: saved output to {output_file}")

        except Exception as e:
            self.logger.error(f"BudgetManagerAgent run error: {e}")
            # 워크플로우 상태 업데이트 등 추가 처리
