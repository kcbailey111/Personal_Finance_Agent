#Author: Kyler Bailey
#Date: January 07, 2026
#Description: Main entry point for the Personal Finance Agent application.

import pandas as pd

# Local agents encapsulate domain logic for ingestion and categorization
from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import CategorizationAgent


def main():
    input_path = "data/raw/transactions.csv"
    output_path = "data/processed/categorized_transactions.csv"

    # Create agents. Each agent is responsible for a single concern:
    # - IngestionAgent: reading/parsing raw data into transaction objects
    # - CategorizationAgent: applying categorization rules or ML models
    ingestion_agent = IngestionAgent(input_path)
    categorization_agent = CategorizationAgent()

    # Load raw transactions (list of transaction objects)
    transactions = ingestion_agent.load_transactions()

    # Apply categorization logic; result is an iterable of transactions
    # enriched with category information
    categorized = categorization_agent.categorize(transactions)

    # Convert transactions (objects) into a pandas DataFrame. Using
    # [t.__dict__ for t in categorized] assumes each transaction exposes
    # its data as attributes; this keeps DataFrame construction simple.
    df = pd.DataFrame([t.__dict__ for t in categorized])

    # Persist to CSV. index=False avoids writing pandas' index column.
    df.to_csv(output_path, index=False)

    # Informational logs — consider replacing prints with structured
    # logging in future refactor for better observability.
    print(f"Processed {len(df)} transactions.")
    print(f"Saved output to {output_path}")


if __name__ == "__main__":
    main()
