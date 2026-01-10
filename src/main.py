# Author: Kyler Bailey
# Date: January 07, 2026
# Description: Main entry point for the Personal Finance Agent application.

import pandas as pd
from pathlib import Path
from dataclasses import asdict

from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import CategorizationAgent
from agents.llm_categorization_agent import LLMCategorizationAgent
from agents.routing import route_transaction


def main():
    # Resolve base directory safely
    BASE_DIR = Path(__file__).resolve().parents[1]


    input_path = BASE_DIR / "data" / "raw" / "transactions.csv"
    output_path = BASE_DIR / "data" / "processed" / "categorized_transactions.csv"

    # Initialize agents
    ingestion_agent = IngestionAgent(input_path)
    rule_agent = CategorizationAgent()
    llm_agent = LLMCategorizationAgent()

    # Load transactions as dictionaries
    transactions = ingestion_agent.load_transactions()

    results = []
    llm_calls = 0

    for transaction in transactions:

        transaction_dict = dict(transaction)

        try:
            rule_result = rule_agent.categorize(transaction)

            final_result, used_llm = route_transaction(
                rule_result=rule_result,
                transaction=transaction_dict,
                llm_agent=llm_agent,
                return_llm_flag=True
            )

            if used_llm:
                llm_calls += 1

        except Exception as e:
            final_result = {
                "category": "Uncategorized",
                "confidence": 0.0,
                "reason": f"Categorization error: {str(e)}"
            }

        results.append({**transaction, **final_result})


    # Persist results
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)

    print(f"Looking for input file at: {input_path}")

    print(f"Processed {len(output_df)} transactions.")
    print(f"LLM used for {llm_calls} transactions.")
    print(f"Saved output to {output_path}")


if __name__ == "__main__":

    main()
