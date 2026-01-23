# Author: Kyler Bailey
# Date: January 07, 2026
# Description: Main entry point for the Personal Finance Agent application.

import pandas as pd
from pathlib import Path

from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import CategorizationAgent
from agents.llm_categorization_agent import LLMCategorizationAgent
from agents.routing import route_transaction
from agents.anomaly_detection_agent import AnomalyDetectionAgent
from tools.expense_stats import ExpenseAnalytics


def main():
    BASE_DIR = Path(__file__).resolve().parents[1]

    input_path = BASE_DIR / "data" / "raw" / "transactions.csv"
    output_path = BASE_DIR / "data" / "processed" / "categorized_transactions.csv"

    ingestion_agent = IngestionAgent(input_path)
    rule_agent = CategorizationAgent()
    llm_agent = LLMCategorizationAgent()

    transactions = ingestion_agent.load_transactions()

    results = []
    llm_calls = 0

    for transaction in transactions:
        transaction_dict = dict(transaction)

        try:
            rule_result = rule_agent.categorize(transaction)

            final_result = route_transaction(
                rule_result=rule_result,
                transaction=transaction_dict,
                llm_agent=llm_agent
            )

            if final_result.get("source") == "llm":
                llm_calls += 1

        except Exception as e:
            final_result = {
                "category": "Uncategorized",
                "confidence": 0.0,
                "source": "error",
                "reason": f"Categorization error: {str(e)}"
            }

        results.append({**transaction, **final_result})

    output_df = pd.DataFrame(results)
    
    # Detect anomalies
    anomaly_agent = AnomalyDetectionAgent()
    output_df = anomaly_agent.detect_anomalies(output_df)
    
    output_df.to_csv(output_path, index=False)

    print(f"Looking for input file at: {input_path}")
    print(f"Processed {len(output_df)} transactions.")
    print(f"LLM used for {llm_calls} transactions.")
    print(f"Saved output to {output_path}")
    
    # Generate and display analytics dashboard
    print("\n")
    analytics = ExpenseAnalytics(output_df)
    analytics_report = analytics.generate_summary_report()
    print(analytics_report)
    
    # Generate and display anomaly detection report
    print("\n")
    anomaly_report = anomaly_agent.generate_anomaly_report(output_df)
    print(anomaly_report)
    
    # Save analytics summary to file
    analytics_output_path = BASE_DIR / "data" / "processed" / "spending_summary.txt"
    analytics.save_summary_to_file(analytics_output_path)
    print(f"\nAnalytics summary saved to: {analytics_output_path}")
    
    # Save monthly summary to CSV file
    monthly_summary = analytics.get_monthly_summary()
    monthly_output_path = BASE_DIR / "data" / "processed" / "monthly_summary.csv"
    if not monthly_summary.empty:
        monthly_summary.to_csv(monthly_output_path, index=False)
        print(f"Monthly summary saved to: {monthly_output_path}")
    else:
        print(f"Warning: No monthly summary data to save.")
    
    # Save anomaly report to file
    anomaly_output_path = BASE_DIR / "data" / "processed" / "anomaly_report.txt"
    anomaly_output_path.write_text(anomaly_report, encoding='utf-8')
    print(f"Anomaly report saved to: {anomaly_output_path}")


if __name__ == "__main__":
    main()
