from typing import List
from utils.schema import Transaction


# Simple in-memory keyword map for categories. Each category maps to a list
# of lowercase keywords that should match against the merchant string.
# Keep rules small and explicit for predictable behavior in tests and demos.
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
            # Flag to indicate whether any rule matched this transaction
            matched = False

            # Normalizing merchant text once per transaction for efficiency
            merchant_lower = txn.merchant.lower()

            # Iterate the category rules in deterministic order and stop on
            # the first keyword match. This makes the behavior predictable
            # (good for tests) but means rule ordering matters when keywords
            # overlap between categories.
            for category, keywords in CATEGORY_RULES.items():
                if any(keyword in merchant_lower for keyword in keywords):
                    # Assign high confidence for explicit rule matches
                    txn.category = category
                    txn.category_confidence = 0.9
                    matched = True
                    break

            # If nothing matched, mark as 'Uncategorized' with lower
            # confidence so downstream code can treat it specially (e.g.,
            # show to the user for manual labeling or apply fallback rules).
            if not matched:
                txn.category = "Uncategorized"
                txn.category_confidence = 0.3

        return transactions
