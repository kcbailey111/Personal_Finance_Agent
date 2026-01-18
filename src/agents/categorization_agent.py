from typing import Dict, Any

CATEGORY_RULES = {
    "Food": ["mcdonald", "chipotle", "restaurant", "cafe", "starbucks"],
    "Transportation": ["uber", "lyft", "shell", "exxon", "chevron"],
    "Subscriptions": ["netflix", "spotify", "amazon prime"],
    "Utilities": ["electric", "water", "internet", "verizon"],
    "Housing": ["rent", "mortgage"],
}


class CategorizationAgent:
    def categorize(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        assert isinstance(txn, dict), f"Expected dict, got {type(txn)}"

        merchant = str(txn.get("merchant", "")).lower()

        for category, keywords in CATEGORY_RULES.items():
            if any(keyword in merchant for keyword in keywords):
                return {
                    "category": category,
                    "confidence": 0.9,
                    "reason": f"Matched keyword rule for {category}"
                }

        # No rule matched → low confidence, escalate later
        return {
            "category": "Uncategorized",
            "confidence": 0.3,
            "reason": "No matching keyword rules"
        }
