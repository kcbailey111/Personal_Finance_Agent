from typing import List, Dict, Any


# Simple in-memory keyword map for categories.
CATEGORY_RULES = {
    "Food": ["mcdonald", "chipotle", "restaurant", "cafe", "starbucks"],
    "Transportation": ["uber", "lyft", "shell", "exxon", "chevron"],
    "Subscriptions": ["netflix", "spotify", "amazon prime"],
    "Utilities": ["electric", "water", "internet", "verizon"],
    "Housing": ["rent", "mortgage"],
}


class CategorizationAgent:
    def categorize(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for txn in transactions:
            matched = False

            # Defensive guard (important in real pipelines)
            merchant = txn.get("merchant", "")
            merchant_lower = merchant.lower()

            for category, keywords in CATEGORY_RULES.items():
                if any(keyword in merchant_lower for keyword in keywords):
                    txn["category"] = category
                    txn["category_confidence"] = 0.9
                    matched = True
                    break

            if not matched:
                txn["category"] = "Uncategorized"
                txn["category_confidence"] = 0.3

        return transactions
