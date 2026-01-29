import unittest
import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agents.recommendation_agent import RecommendationAgent  # noqa: E402


class TestRecommendationAgent(unittest.TestCase):
    def test_generates_recommendations_offline(self):
        df = pd.DataFrame(
            [
                {"date": "2026-01-01", "amount": 99.0, "category": "Shopping", "description": "Amazon", "tags": ""},
                {"date": "2026-01-15", "amount": 25.0, "category": "Dining", "description": "Restaurant", "tags": "recurring"},
                {"date": "2026-01-20", "amount": 25.0, "category": "Dining", "description": "Restaurant", "tags": "recurring"},
                {"date": "2026-01-25", "amount": 25.0, "category": "Dining", "description": "Restaurant", "tags": "recurring"},
                {"date": "2026-01-28", "amount": 12.0, "category": "Uncategorized", "description": "Unknown", "tags": ""},
                {"date": "2026-01-29", "amount": 12.0, "category": "Uncategorized", "description": "Unknown2", "tags": ""},
                {"date": "2026-01-30", "amount": 500.0, "category": "Shopping", "description": "Big Purchase", "is_anomaly": True},
            ]
        )
        agent = RecommendationAgent(enabled=False)
        recs = agent.generate_recommendations(df)
        self.assertIsInstance(recs, dict)
        self.assertIn("recommendations", recs)
        self.assertGreaterEqual(len(recs["recommendations"]), 1)


if __name__ == "__main__":
    unittest.main()

