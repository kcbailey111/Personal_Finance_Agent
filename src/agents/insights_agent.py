"""
Insights Agent

Generates structured insights + a short narrative from transaction data.
Works without an LLM; if LLM is enabled, it will optionally enhance the narrative.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from config.settings import LLM_ENABLED, OPENAI_API_KEY, OPENAI_INSIGHTS_MODEL
from tools.expense_stats import ExpenseAnalytics


@dataclass(frozen=True)
class InsightsConfig:
    top_n_categories: int = 5


class InsightsAgent:
    def __init__(self, config: InsightsConfig | None = None, enabled: bool | None = None):
        self.config = config or InsightsConfig()
        self.enabled = LLM_ENABLED if enabled is None else bool(enabled)
        self._client = None
        if self.enabled and OPENAI_API_KEY:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception:
                self._client = None

    @staticmethod
    def _safe_float(x: Any, default: float = 0.0) -> float:
        try:
            return float(x)
        except Exception:
            return default

    def _basic_insights(self, df: pd.DataFrame) -> dict[str, Any]:
        analytics = ExpenseAnalytics(df)
        cat = analytics.get_category_summary().head(self.config.top_n_categories)
        monthly = analytics.get_monthly_summary()

        insights: list[dict[str, Any]] = []
        if not cat.empty:
            top = cat.iloc[0]
            insights.append(
                {
                    "type": "top_category",
                    "text": f"Top category is {top['category']} at ${self._safe_float(top['total_spent']):,.2f} "
                    f"({self._safe_float(top['percentage']):.1f}% of total).",
                }
            )

        if len(monthly) >= 2:
            last = monthly.iloc[-1]
            prev = monthly.iloc[-2]
            delta = self._safe_float(last["total_spent"]) - self._safe_float(prev["total_spent"])
            pct = (delta / max(self._safe_float(prev["total_spent"]), 1e-9)) * 100.0
            insights.append(
                {
                    "type": "month_over_month",
                    "text": f"Month-over-month spending changed by ${delta:,.2f} ({pct:+.1f}%).",
                }
            )

        # Anomalies
        if "is_anomaly" in df.columns:
            anom_count = int((df["is_anomaly"] == True).sum())  # noqa: E712
            if anom_count:
                insights.append(
                    {
                        "type": "anomalies",
                        "text": f"{anom_count} transactions were flagged as anomalies. Review them for potential fraud or one-offs.",
                    }
                )

        # Recurring
        if "tags" in df.columns:
            recurring_count = int(df["tags"].astype(str).str.contains("recurring", na=False).sum())
            if recurring_count:
                insights.append(
                    {
                        "type": "recurring",
                        "text": f"{recurring_count} transactions look recurring (subscriptions/bills). Consider auditing them.",
                    }
                )

        recommendations: list[str] = []
        recommendations.extend(
            [
                "Review your top 1–2 spending categories and pick a small, realistic cut for next month.",
                "Audit recurring charges and cancel anything unused.",
            ]
        )

        payload = {
            "insights": insights,
            "recommendations": recommendations,
            "summary_stats": {
                "total_spending": analytics.get_total_spending(),
                "transaction_count": analytics.get_transaction_count(),
            },
            "top_categories": cat.to_dict(orient="records") if not cat.empty else [],
            "monthly_summary": monthly.to_dict(orient="records") if not monthly.empty else [],
        }
        return payload

    def generate_insights(self, transactions_df: pd.DataFrame) -> dict[str, Any]:
        payload = self._basic_insights(transactions_df)

        if self._client is None:
            payload["narrative"] = " ".join([i["text"] for i in payload.get("insights", [])]) or "No insights available."
            return payload

        try:
            prompt = (
                "You are a helpful personal finance analyst. Using the JSON stats below, "
                "write a short, friendly narrative summary (4-8 sentences) and return JSON:\n"
                "{narrative: string, extra_recommendations: [string]}.\n\n"
                f"Stats JSON:\n{json.dumps(payload, indent=2)}"
            )
            resp = self._client.chat.completions.create(
                model=OPENAI_INSIGHTS_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            content = (resp.choices[0].message.content or "").strip()
            enriched = json.loads(content)
            if isinstance(enriched, dict):
                if "narrative" in enriched:
                    payload["narrative"] = enriched["narrative"]
                if "extra_recommendations" in enriched and isinstance(enriched["extra_recommendations"], list):
                    payload["recommendations"] = payload.get("recommendations", []) + enriched["extra_recommendations"]
        except Exception:
            payload["narrative"] = " ".join([i["text"] for i in payload.get("insights", [])]) or "No insights available."

        return payload

