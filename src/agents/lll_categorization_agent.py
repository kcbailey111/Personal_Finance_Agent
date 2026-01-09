import openai
import json
from config.settings import OPENAI_API_KEY
from config.categories import ALLOWED_CATEGORIES

openai.api_key = OPENAI_API_KEY


SYSTEM_PROMPT = """
You are a financial transaction categorization agent.

You must return ONLY valid JSON.
Do not include markdown or explanations outside JSON.
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
    def categorize(self, transaction: dict) -> dict:
        prompt = USER_PROMPT_TEMPLATE.format(
            description=transaction["description"],
            amount=transaction["amount"],
            date=transaction["date"],
            categories="\n".join(ALLOWED_CATEGORIES),
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        content = response["choices"][0]["message"]["content"]

        return json.loads(content)
