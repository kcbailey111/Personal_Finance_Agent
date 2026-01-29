# Author: Kyler Bailey
# Date: January 07, 2026
# Description: Main entry point for the Personal Finance Agent application.

import pandas as pd
import argparse
import json
from pathlib import Path

from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import CategorizationAgent
from agents.llm_categorization_agent import LLMCategorizationAgent
from agents.routing import route_transaction
from agents.anomaly_detection_agent import AnomalyDetectionAgent
from agents.enrichment_agent import EnrichmentAgent
from agents.bill_agent import BillAgent
from agents.insights_agent import InsightsAgent
from agents.recommendation_agent import RecommendationAgent
from agents.forecasting_agent import ForecastingAgent, ForecastConfig
from agents.budget_agent import BudgetAgent
from agents.health_agent import FinancialHealthAgent
from agents.chat_agent import ChatAgent
from tools.expense_stats import ExpenseAnalytics
from tools.ai_visualization import AIVisualizationTool


def main():
    parser = argparse.ArgumentParser(description="Personal Finance Agent")
    parser.add_argument("--no-llm", action="store_true", help="Disable all LLM usage (offline mode).")
    parser.add_argument("--ask", type=str, default="", help="Ask a question about your finances (CLI chat).")
    parser.add_argument("--months-ahead", type=int, default=3, help="Forecast months ahead.")
    parser.add_argument("--dashboard", action="store_true", help="Generate an offline HTML dashboard.")
    args = parser.parse_args()

    BASE_DIR = Path(__file__).resolve().parents[1]

    input_path = BASE_DIR / "data" / "raw" / "transactions.csv"
    output_path = BASE_DIR / "data" / "processed" / "categorized_transactions.csv"
    processed_dir = BASE_DIR / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    ingestion_agent = IngestionAgent(input_path)
    rule_agent = CategorizationAgent()
    llm_agent = LLMCategorizationAgent(enabled=not args.no_llm)

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
    # Optional: add short LLM explanations for anomalies
    output_df = anomaly_agent.add_ai_explanations(output_df, enabled=(not args.no_llm))

    # Enrich + tag transactions (offline)
    enrichment_agent = EnrichmentAgent()
    output_df = enrichment_agent.enrich_dataframe(output_df)

    # Detect recurring bills/subscriptions (offline)
    bill_agent = BillAgent()
    output_df = bill_agent.mark_recurring(output_df)
    
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

    # Save bill calendar
    bill_calendar = bill_agent.build_bill_calendar(output_df)
    bill_calendar_path = processed_dir / "bill_calendar.csv"
    bill_calendar.to_csv(bill_calendar_path, index=False)
    print(f"Bill calendar saved to: {bill_calendar_path}")

    # AI insights + recommendations
    insights_agent = InsightsAgent(enabled=(not args.no_llm))
    insights = insights_agent.generate_insights(output_df)
    insights_path = processed_dir / "ai_insights.json"
    insights_path.write_text(json.dumps(insights, indent=2), encoding="utf-8")
    print(f"AI insights saved to: {insights_path}")

    rec_agent = RecommendationAgent(enabled=(not args.no_llm))
    recs = rec_agent.generate_recommendations(output_df)
    recs_path = processed_dir / "ai_recommendations.json"
    recs_path.write_text(json.dumps(recs, indent=2), encoding="utf-8")
    print(f"AI recommendations saved to: {recs_path}")

    # Forecasting
    forecasting_agent = ForecastingAgent(config=ForecastConfig(months_ahead=max(1, args.months_ahead)))
    forecast_df = forecasting_agent.forecast_spending(output_df)
    forecast_path = processed_dir / "spending_forecast.csv"
    forecast_df.to_csv(forecast_path, index=False)
    print(f"Spending forecast saved to: {forecast_path}")

    # Smart budget + budget status (uses YAML rules if present; otherwise generates from history)
    budget_agent = BudgetAgent()
    budget_rules_path = BASE_DIR / "data" / "rules" / "budget_rules.yaml"
    budgets = budget_agent.load_budget_rules(budget_rules_path) or budget_agent.generate_smart_budget(output_df).get("budgets", {})
    budget_status = budget_agent.budget_status(output_df, budgets)
    budget_status_path = processed_dir / "budget_status.json"
    budget_status_path.write_text(json.dumps(budget_status, indent=2), encoding="utf-8")
    print(f"Budget status saved to: {budget_status_path}")

    # Financial health score
    health_agent = FinancialHealthAgent()
    health = health_agent.calculate(output_df, budget_status=budget_status)
    health_path = processed_dir / "financial_health.json"
    health_path.write_text(json.dumps(health, indent=2), encoding="utf-8")
    print(f"Financial health saved to: {health_path}")

    # Optional offline HTML dashboard
    if args.dashboard:
        dashboard_tool = AIVisualizationTool()
        dashboard_path = processed_dir / "dashboard.html"
        dashboard_tool.generate_smart_dashboard(output_df, dashboard_path)
        print(f"Dashboard saved to: {dashboard_path}")

    # Optional conversational query
    if args.ask.strip():
        chat_agent = ChatAgent(enabled=(not args.no_llm))
        chat_answer = chat_agent.query(args.ask.strip(), output_df)
        print("\n" + "=" * 60)
        print("CHAT ANSWER")
        print("=" * 60)
        print(chat_answer.answer)
        if chat_answer.data_preview:
            print("\nPreview:\n")
            print(chat_answer.data_preview)


if __name__ == "__main__":
    main()
