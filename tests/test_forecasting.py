import unittest
import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agents.forecasting_agent import ForecastingAgent, ForecastConfig  # noqa: E402


class TestForecastingAgent(unittest.TestCase):
    def test_forecast_spending_returns_rows(self):
        df = pd.DataFrame(
            [
                {"date": "2026-01-05", "amount": 10, "category": "Groceries", "description": "A"},
                {"date": "2026-01-20", "amount": 20, "category": "Groceries", "description": "B"},
                {"date": "2026-02-03", "amount": 15, "category": "Dining", "description": "C"},
                {"date": "2026-02-14", "amount": 25, "category": "Dining", "description": "D"},
            ]
        )
        agent = ForecastingAgent(config=ForecastConfig(months_ahead=2, granularity="category"))
        out = agent.forecast_spending(df)
        self.assertFalse(out.empty)
        self.assertIn("month", out.columns)
        self.assertIn("category", out.columns)
        self.assertIn("forecast_total_spent", out.columns)
        self.assertGreaterEqual(len(out), 2)  # at least one category * months_ahead

    def test_forecast_non_negative(self):
        df = pd.DataFrame([{"date": "2026-01-01", "amount": 0.0, "category": "Groceries", "description": "A"}])
        agent = ForecastingAgent(config=ForecastConfig(months_ahead=3, granularity="category"))
        out = agent.forecast_spending(df)
        self.assertTrue((out["forecast_total_spent"] >= 0).all())


if __name__ == "__main__":
    unittest.main()

