import json
from typing import Dict

from openai import OpenAI
from config.settings import LLM_ENABLED, OPENAI_API_KEY, OPENAI_CATEGORIZATION_MODEL
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
    def __init__(self, enabled: bool | None = None):
        self.enabled = LLM_ENABLED if enabled is None else bool(enabled)
        self.disabled_reason = ""

        if not self.enabled:
            self.disabled_reason = "LLM is disabled (LLM_ENABLED=false)"
            self.client = None
            return

        if not OPENAI_API_KEY:
            self.enabled = False
            self.disabled_reason = "OPENAI_API_KEY missing; running in non-LLM mode"
            self.client = None
            return

        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def is_enabled(self) -> bool:
        return bool(self.enabled and self.client is not None)

    def categorize(self, transaction: Dict) -> Dict:
        if not self.is_enabled():
            return {
                "category": "Uncategorized",
                "confidence": 0.0,
                "reason": self.disabled_reason or "LLM is not available",
            }

        prompt = USER_PROMPT_TEMPLATE.format(
            description=transaction.get("description", ""),
            amount=transaction.get("amount", 0),
            date=transaction.get("date", ""),
            categories="\n".join(ALLOWED_CATEGORIES),
        )

        response = self.client.chat.completions.create(
            model=OPENAI_CATEGORIZATION_MODEL,
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
