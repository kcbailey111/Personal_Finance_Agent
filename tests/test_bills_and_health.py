import unittest
import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agents.bill_agent import BillAgent  # noqa: E402
from agents.health_agent import FinancialHealthAgent  # noqa: E402


class TestBillsAndHealth(unittest.TestCase):
    def test_bill_agent_marks_recurring(self):
        df = pd.DataFrame(
            [
                {"date": "2025-11-01", "amount": 9.99, "merchant": "Netflix", "description": "Netflix"},
                {"date": "2025-12-01", "amount": 9.99, "merchant": "Netflix", "description": "Netflix"},
                {"date": "2026-01-01", "amount": 9.99, "merchant": "Netflix", "description": "Netflix"},
                {"date": "2026-01-15", "amount": 40.0, "merchant": "Grocery", "description": "Food"},
            ]
        )
        agent = BillAgent()
        out = agent.mark_recurring(df)
        self.assertIn("is_recurring", out.columns)
        self.assertGreaterEqual(int((out["is_recurring"] == True).sum()), 1)  # noqa: E712

    def test_health_agent_returns_score_range(self):
        df = pd.DataFrame(
            [
                {"date": "2026-01-01", "amount": 100.0, "category": "Groceries"},
                {"date": "2026-01-15", "amount": 50.0, "category": "Dining"},
                {"date": "2026-02-01", "amount": 110.0, "category": "Groceries"},
                {"date": "2026-02-15", "amount": 60.0, "category": "Dining"},
            ]
        )
        agent = FinancialHealthAgent()
        res = agent.calculate(df, budget_status=None)
        self.assertIn("score", res)
        self.assertGreaterEqual(res["score"], 0)
        self.assertLessEqual(res["score"], 100)


if __name__ == "__main__":
    unittest.main()

