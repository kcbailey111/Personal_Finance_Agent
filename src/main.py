# Author: Kyler Bailey
# Date: January 07, 2026
# Description: Main entry point for the Personal Finance Agent application.

import pandas as pd
from pathlib import Path

from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import RuleCategorizationAgent
from agents.lll_categorization_agent import LLMCategorizationAgent
from agents.routing import route_transaction


def main():
    # Resolve base directory
    BASE_DIR = Path(__file__).resolve().parent.parent

    input_path = BASE_DIR / "data" / "raw" / "transactions.csv"
    output_path = BASE_DIR / "data" / "processed" / "categorized_transactions.csv"

    # Initialize agents
    ingestion_agent = IngestionAgent(input_path)
    rule_agent = RuleCategorizationAgent()
    llm_agent = LLMCategorizationAgent()

    # Load transactions as dictionaries
    transactions = ingestion_agent.load_transactions()

    results = []

    for transaction in transactions:
        # Apply rule-based categorization
        rule_result = rule_agent.categorize(transaction)

        # Route decision (rule vs LLM)
        final_result = route_transaction(
            rule_result=rule_result,
            transaction=transaction,
            llm_agent=llm_agent
        )

        results.append({**transaction, **final_result})

    # Persist results
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)

    print(f"Processed {len(output_df)} transactions.")
    print(f"Saved output to {output_path}")


if __name__ == "__main__":
    main()
