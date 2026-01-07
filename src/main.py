#Author: Kyler Bailey
#Date: January 07, 2026
#Description: Main entry point for the Personal Finance Agent application.

import pandas as pd

from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import CategorizationAgent


def main():
    input_path = "data/raw/transactions.csv"
    output_path = "data/processed/categorized_transactions.csv"

    ingestion_agent = IngestionAgent(input_path)
    categorization_agent = CategorizationAgent()

    transactions = ingestion_agent.load_transactions()
    categorized = categorization_agent.categorize(transactions)

    df = pd.DataFrame([t.__dict__ for t in categorized])
    df.to_csv(output_path, index=False)

    print(f"Processed {len(df)} transactions.")
    print(f"Saved output to {output_path}")


if __name__ == "__main__":
    main()
