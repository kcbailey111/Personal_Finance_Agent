import json
from typing import Dict

from openai import OpenAI
from config.settings import OPENAI_API_KEY
from config.categories import ALLOWED_CATEGORIES


SYSTEM_PROMPT = """
You are a financial transaction categorization engine.

Rules:
- Respond ONLY with valid JSON.
- Do NOT include markdown.
- Do NOT include explanations outside JSON.
- Output MUST be parseable by json.loads().
"""

USER_PROMPT_TEMPLATE = """
Transaction details:
- Description: "{description}"
- Amount: {amount}
- Date: {date}

Allowed categories:
{categories}

Return a JSON object with:
- category
- confidence (0 to 1)
- reason

Rules:
- Choose exactly one category.
- If confidence < 0.5, category MUST be "Uncategorized".
"""


class LLMCategorizationAgent:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def categorize(self, transaction: Dict) -> Dict:
        prompt = USER_PROMPT_TEMPLATE.format(
            description=transaction.get("description", ""),
            amount=transaction.get("amount", 0),
            date=transaction.get("date", ""),
            categories="\n".join(ALLOWED_CATEGORIES),
        )

        response = self.client.chat.completions.create(
            model="gpt-5-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content.strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            return {
                "category": "Uncategorized",
                "confidence": 0.0,
                "reason": "LLM returned invalid JSON"
            }

        # Defensive normalization
        category = result.get("category", "Uncategorized")
        confidence = float(result.get("confidence", 0))
        reason = result.get("reason", "No explanation provided")

        if confidence < 0.5:
            category = "Uncategorized"

        return {
            "category": category,
            "confidence": confidence,
            "reason": reason
        }
