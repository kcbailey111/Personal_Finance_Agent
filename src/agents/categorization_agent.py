from typing import List
from utils.schema import Transaction


CATEGORY_RULES = {
    "Food": ["mcdonald", "chipotle", "restaurant", "cafe", "starbucks"],
    "Transportation": ["uber", "lyft", "shell", "exxon", "chevron"],
    "Subscriptions": ["netflix", "spotify", "amazon prime"],
    "Utilities": ["electric", "water", "internet", "verizon"],
    "Housing": ["rent", "mortgage"],
}


class CategorizationAgent:
    def categorize(self, transactions: List[Transaction]) -> List[Transaction]:
        for txn in transactions:
            matched = False
            merchant_lower = txn.merchant.lower()

            for category, keywords in CATEGORY_RULES.items():
                if any(keyword in merchant_lower for keyword in keywords):
                    txn.category = category
                    txn.category_confidence = 0.9
                    matched = True
                    break

            if not matched:
                txn.category = "Uncategorized"
                txn.category_confidence = 0.3

        return transactions
