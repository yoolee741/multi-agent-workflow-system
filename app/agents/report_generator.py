import os
import json
from pathlib import Path
from openai import OpenAI
from app.agents.base import BaseAgent

class ReportGeneratorAgent(BaseAgent):
    async def run(self):
        try:
            client = OpenAI(
                base_url="https://api.deepauto.ai/openai/v1",
                api_key=os.getenv("API_KEY"),
            )

            # 1) 이전 agent 결과 읽기 (파일에서)
            itinerary_file = self.input_path / "itinerary.json"
            budget_file = self.input_path / "budget.json"

            if not itinerary_file.exists():
                self.logger.error(f"Input file not found: {itinerary_file}")
                return
            if not budget_file.exists():
                self.logger.error(f"Input file not found: {budget_file}")
                return

            with itinerary_file.open("r", encoding="utf-8") as f:
                itinerary_json = json.loads(f.read())
            with budget_file.open("r", encoding="utf-8") as f:
                budget_json = json.loads(f.read())

            pretty_itinerary = json.dumps(itinerary_json, indent=2)
            pretty_budget = json.dumps(budget_json, indent=2)

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

            # TODO: 파일 저장 대신 DB 저장 필요 시 변경 가능
            output_file = self.output_path / "report.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(response_text, encoding="utf-8")

            self.logger.info(f"ReportGeneratorAgent: saved output to {output_file}")

        except Exception as e:
            self.logger.error(f"ReportGeneratorAgent run error: {e}")
            # 워크플로우 상태 업데이트 등 추가 처리 가능
