import unittest
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agents.llm_categorization_agent import LLMCategorizationAgent  # noqa: E402
from agents.routing import route_transaction  # noqa: E402


class TestCategorizationRouting(unittest.TestCase):
    def test_llm_agent_disabled_returns_uncategorized(self):
        agent = LLMCategorizationAgent(enabled=False)
        out = agent.categorize({"description": "Test", "amount": 10, "date": "2026-01-01"})
        self.assertEqual(out["category"], "Uncategorized")
        self.assertEqual(out["confidence"], 0.0)

    def test_route_transaction_falls_back_when_no_llm(self):
        rule_result = {"category": "Dining", "confidence": 0.2, "reason": "low"}
        tx = {"description": "Restaurant", "amount": 10, "date": "2026-01-01"}
        agent = LLMCategorizationAgent(enabled=False)
        out = route_transaction(rule_result=rule_result, transaction=tx, llm_agent=agent)
        self.assertEqual(out["source"], "rule_no_llm")
        self.assertEqual(out["category"], "Dining")


if __name__ == "__main__":
    unittest.main()

