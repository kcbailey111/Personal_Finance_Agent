from typing import Dict, Any


# Simple in-memory keyword map for categories.
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
        matched = False

        for category, keywords in CATEGORY_RULES.items():
            if any(keyword in merchant for keyword in keywords):
                txn["category"] = category
                txn["category_confidence"] = 0.9
                matched = True
                break

        if not matched:
            txn["category"] = "Uncategorized"
            txn["category_confidence"] = 0.3

        return txn
