"""
Financial Health Score Agent

Computes a simple explainable 0-100 score from transaction data:
- volatility of monthly spending
- share of discretionary categories
- anomaly rate
- (optional) budget adherence
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class HealthConfig:
    discretionary_categories: tuple[str, ...] = ("Dining", "Entertainment", "Shopping")
    weight_volatility: float = 0.35
    weight_discretionary: float = 0.30
    weight_anomalies: float = 0.20
    weight_budget: float = 0.15


class FinancialHealthAgent:
    def __init__(self, config: HealthConfig | None = None):
        self.config = config or HealthConfig()

    @staticmethod
    def _prepare(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["amount"] = pd.to_numeric(out.get("amount"), errors="coerce")
        out["date"] = pd.to_datetime(out.get("date"), errors="coerce")
        out = out.dropna(subset=["amount", "date"])
        if "category" not in out.columns:
            out["category"] = "Uncategorized"
        out["year_month"] = out["date"].dt.to_period("M").dt.to_timestamp()
        return out

    @staticmethod
    def _clamp01(x: float) -> float:
        return float(max(0.0, min(1.0, x)))

    def calculate(self, transactions_df: pd.DataFrame, budget_status: dict[str, Any] | None = None) -> dict[str, Any]:
        df = self._prepare(transactions_df)
        if df.empty:
            return {"score": 0, "reasons": ["No valid transactions available."], "components": {}}

        # monthly volatility (std/mean)
        monthly = df.groupby("year_month", as_index=False).agg(total=("amount", "sum")).sort_values("year_month")
        totals = monthly["total"].astype(float).to_numpy()
        mean = float(np.mean(totals)) if len(totals) else 0.0
        std = float(np.std(totals)) if len(totals) else 0.0
        volatility = (std / mean) if mean > 1e-9 else 0.0
        # map: volatility 0 -> good, >=1 -> bad
        vol_score = 1.0 - self._clamp01(volatility / 1.0)

        # discretionary share
        disc = df[df["category"].isin(self.config.discretionary_categories)]
        disc_share = float(disc["amount"].sum() / max(float(df["amount"].sum()), 1e-9))
        disc_score = 1.0 - self._clamp01(disc_share / 0.6)  # 60%+ discretionary => very low

        # anomalies
        if "is_anomaly" in df.columns:
            anom_rate = float((df["is_anomaly"] == True).mean())  # noqa: E712
        else:
            anom_rate = 0.0
        anom_score = 1.0 - self._clamp01(anom_rate / 0.2)  # 20% anomalies => very low

        # budget adherence
        budget_over_ratio = 0.0
        if budget_status and isinstance(budget_status, dict):
            cats = budget_status.get("categories") or []
            if isinstance(cats, list) and cats:
                overs = [c for c in cats if c.get("over_budget") is True]
                budget_over_ratio = len(overs) / len(cats)
        budget_score = 1.0 - self._clamp01(budget_over_ratio / 0.5)  # half categories over => very low

        w = self.config
        score01 = (
            w.weight_volatility * vol_score
            + w.weight_discretionary * disc_score
            + w.weight_anomalies * anom_score
            + w.weight_budget * budget_score
        )
        score = int(round(100.0 * self._clamp01(score01)))

        reasons: list[str] = []
        if volatility > 0.5:
            reasons.append("Monthly spending varies a lot month-to-month.")
        if disc_share > 0.4:
            reasons.append("A large share of spending is discretionary (Dining/Entertainment/Shopping).")
        if anom_rate > 0.05:
            reasons.append("There are several flagged anomalies—review for fraud or one-offs.")
        if budget_over_ratio > 0.2:
            reasons.append("Multiple categories are currently over budget.")
        if not reasons:
            reasons.append("Overall spending patterns look stable.")

        return {
            "score": score,
            "reasons": reasons,
            "components": {
                "volatility": round(volatility, 3),
                "discretionary_share": round(disc_share, 3),
                "anomaly_rate": round(anom_rate, 3),
                "budget_over_ratio": round(budget_over_ratio, 3),
            },
        }

