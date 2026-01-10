# Author: Kyler Bailey
# Date: January 07, 2026
# Description: Main entry point for the Personal Finance Agent application.

import pandas as pd
from pathlib import Path

from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import RuleCategorizationAgent
from agents.llm_categorization_agent import LLMCategorizationAgent
from agents.routing import route_transaction


def main():
    # Resolve base directory safely
    BASE_DIR = Path(__file__).resolve().parent

    input_path = BASE_DIR / "data" / "raw" / "transactions.csv"
    output_path = BASE_DIR / "data" / "processed" / "categorized_transactions.csv"

    # Initialize agents
    ingestion_agent = IngestionAgent(input_path)
    rule_agent = RuleCategorizationAgent()
    llm_agent = LLMCategorizationAgent()

    # Load transactions as dictionaries
    transactions = ingestion_agent.load_transactions()

    results = []
    llm_calls = 0

    for transaction in transactions:
        try:
            # Apply rule-based categorization
            rule_result = rule_agent.categorize(transaction)

            # Route decision (rule vs LLM)
            final_result, used_llm = route_transaction(
                rule_result=rule_result,
                transaction=transaction,
                llm_agent=llm_agent,
                return_llm_flag=True
            )

            if used_llm:
                llm_calls += 1

        except Exception as e:
            # Fail safe: do not kill batch on LLM or logic error
            final_result = {
                "category": "Uncategorized",
                "confidence": 0.0,
                "reason": f"Categorization error: {str(e)}"
            }

        results.append({**transaction, **final_result})

    # Persist results
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)

    print(f"Processed {len(output_df)} transactions.")
    print(f"LLM used for {llm_calls} transactions.")
    print(f"Saved output to {output_path}")


if __name__ == "__main__":
    main()
