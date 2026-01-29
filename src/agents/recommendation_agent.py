"""
Recommendation Agent

Produces actionable recommendations from spending data (offline heuristics),
optionally upgraded with LLM wording when enabled.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from config.settings import LLM_ENABLED, OPENAI_API_KEY, OPENAI_INSIGHTS_MODEL


@dataclass(frozen=True)
class Recommendation:
    title: str
    rationale: str
    impact: str = "medium"  # low|medium|high
    category: str | None = None


class RecommendationAgent:
    def __init__(self, enabled: bool | None = None):
        self.enabled = LLM_ENABLED if enabled is None else bool(enabled)
        self._client = None
        if self.enabled and OPENAI_API_KEY:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception:
                self._client = None

    def _heuristic_recommendations(self, df: pd.DataFrame) -> list[Recommendation]:
        out: list[Recommendation] = []
        if df.empty:
            return out

        d = df.copy()
        d["amount"] = pd.to_numeric(d.get("amount"), errors="coerce")
        d["date"] = pd.to_datetime(d.get("date"), errors="coerce")
        d = d.dropna(subset=["amount", "date"])
        if "category" not in d.columns:
            d["category"] = "Uncategorized"

        # Top categories
        by_cat = d.groupby("category", as_index=False).agg(total=("amount", "sum")).sort_values("total", ascending=False)
        if not by_cat.empty:
            top = by_cat.iloc[0]
            out.append(
                Recommendation(
                    title=f"Review your spending in {top['category']}",
                    rationale=f"This is your highest-spend category at ${float(top['total']):,.2f}. Identify 1–2 easy cuts.",
                    impact="high",
                    category=str(top["category"]),
                )
            )

        # Recurring/subscription hints (if tags exist)
        if "tags" in d.columns:
            recurring = d[d["tags"].astype(str).str.contains("recurring", na=False)]
            if not recurring.empty:
                monthly = recurring.copy()
                monthly["year_month"] = monthly["date"].dt.strftime("%Y-%m")
                by_month = monthly.groupby("year_month", as_index=False).agg(total=("amount", "sum"))
                avg = float(by_month["total"].mean()) if not by_month.empty else float(recurring["amount"].sum())
                out.append(
                    Recommendation(
                        title="Audit recurring charges",
                        rationale=f"Recurring charges average about ${avg:,.2f} per month. Cancel or downgrade anything unused.",
                        impact="high",
                    )
                )

        # Anomalies
        if "is_anomaly" in d.columns:
            anom = d[d["is_anomaly"] == True]  # noqa: E712
            if not anom.empty:
                out.append(
                    Recommendation(
                        title="Review flagged anomalies",
                        rationale=f"{len(anom)} transactions were flagged as unusual. Verify they’re legitimate and adjust alerts if needed.",
                        impact="medium",
                    )
                )

        # Uncategorized cleanup
        unc = d[d["category"] == "Uncategorized"]
        if len(unc) >= 2:
            out.append(
                Recommendation(
                    title="Improve categorization rules",
                    rationale=f"{len(unc)} transactions are Uncategorized. Add a rule for common merchants to reduce future LLM usage and improve reporting.",
                    impact="medium",
                    category="Uncategorized",
                )
            )

        return out

    def generate_recommendations(self, transactions_df: pd.DataFrame) -> dict[str, Any]:
        recs = self._heuristic_recommendations(transactions_df)
        payload = {
            "recommendations": [
                {"title": r.title, "rationale": r.rationale, "impact": r.impact, "category": r.category} for r in recs
            ]
        }

        # Optional LLM rewrite: better phrasing + extra ideas, but never required.
        if self._client is None:
            return payload

        try:
            prompt = (
                "You are a personal finance coach. Rewrite and enrich these recommendations. "
                "Return JSON: {recommendations:[{title,rationale,impact,category}]}. "
                "Keep it concise and actionable.\n\n"
                f"Input JSON:\n{json.dumps(payload, indent=2)}"
            )
            resp = self._client.chat.completions.create(
                model=OPENAI_INSIGHTS_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            content = (resp.choices[0].message.content or "").strip()
            enhanced = json.loads(content)
            if isinstance(enhanced, dict) and "recommendations" in enhanced:
                return enhanced
        except Exception:
            pass

        return payload

