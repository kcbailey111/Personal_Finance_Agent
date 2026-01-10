import json
from config.settings import OPENAI_API_KEY
from config.categories import ALLOWED_CATEGORIES

from openai import OpenAI



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

client = OpenAI(api_key=OPENAI_API_KEY)


class LLMCategorizationAgent:
    def categorize(self, transaction: dict) -> dict:
        prompt = USER_PROMPT_TEMPLATE.format(
            description=transaction["description"],
            amount=transaction["amount"],
            date=transaction["date"],
            categories="\n".join(ALLOWED_CATEGORIES),
        )

        
        response = client.chat.completions.create(
            model="gpt-5-nano",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content


        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Model returned invalid JSON: {content}")
