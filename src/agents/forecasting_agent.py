"""
Forecasting Agent

Lightweight spending forecasts from historical transactions.
Designed to work offline (no LLM required). If you later want LLM-enhanced
forecast narratives, pair this with InsightsAgent/RecommendationAgent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


ForecastGranularity = Literal["total", "category"]


@dataclass(frozen=True)
class ForecastConfig:
    months_ahead: int = 3
    lookback_months: int = 6
    granularity: ForecastGranularity = "category"


class ForecastingAgent:
    def __init__(self, config: ForecastConfig | None = None):
        self.config = config or ForecastConfig()

    @staticmethod
    def _prepare(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["amount"] = pd.to_numeric(out.get("amount"), errors="coerce")
        out["date"] = pd.to_datetime(out.get("date"), errors="coerce")
        out = out.dropna(subset=["date", "amount"])
        out["year_month"] = out["date"].dt.to_period("M").dt.to_timestamp()
        if "category" not in out.columns:
            out["category"] = "Uncategorized"
        return out

    @staticmethod
    def _future_month_starts(last_month_start: pd.Timestamp, months_ahead: int) -> list[pd.Timestamp]:
        return [
            (last_month_start + pd.offsets.MonthBegin(i)).normalize()
            for i in range(1, months_ahead + 1)
        ]

    @staticmethod
    def _fit_linear(y: np.ndarray) -> tuple[np.ndarray, str]:
        """
        Fit a simple linear trend over indices 0..n-1.
        Returns predicted values for existing points and method label.
        """
        n = len(y)
        if n <= 1:
            return y, "flat"
        x = np.arange(n, dtype=float)
        slope, intercept = np.polyfit(x, y.astype(float), 1)
        return slope * x + intercept, "linear"

    def forecast_spending(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns a DataFrame with forecasts:
        - month (YYYY-MM)
        - category (or 'TOTAL')
        - forecast_total_spent
        - method
        """
        df = self._prepare(transactions_df)
        if df.empty:
            return pd.DataFrame(columns=["month", "category", "forecast_total_spent", "method"])

        if self.config.granularity == "total":
            grouped = (
                df.groupby("year_month", as_index=False)
                .agg(total_spent=("amount", "sum"))
                .sort_values("year_month")
            )
            last = grouped["year_month"].max()
            future = self._future_month_starts(last, self.config.months_ahead)

            # lookback slice
            lookback = grouped.tail(self.config.lookback_months)
            y = lookback["total_spent"].to_numpy()
            _, method = self._fit_linear(y)
            # forecast: continue slope from last two points if possible, else flat
            if len(y) <= 1:
                slope = 0.0
                base = float(y[-1]) if len(y) == 1 else 0.0
            else:
                slope = float(y[-1] - y[-2])
                base = float(y[-1])
            preds = [max(0.0, base + slope * i) for i in range(1, self.config.months_ahead + 1)]

            out = pd.DataFrame(
                {
                    "month": [d.strftime("%Y-%m") for d in future],
                    "category": ["TOTAL"] * len(future),
                    "forecast_total_spent": [round(v, 2) for v in preds],
                    "method": [method] * len(future),
                }
            )
            return out

        # category-level
        grouped = (
            df.groupby(["category", "year_month"], as_index=False)
            .agg(total_spent=("amount", "sum"))
            .sort_values(["category", "year_month"])
        )
        last_month = grouped["year_month"].max()
        future_months = self._future_month_starts(last_month, self.config.months_ahead)

        rows: list[dict] = []
        for category, cdf in grouped.groupby("category"):
            lookback = cdf.tail(self.config.lookback_months)
            y = lookback["total_spent"].to_numpy()
            _, method = self._fit_linear(y)

            if len(y) <= 1:
                slope = 0.0
                base = float(y[-1]) if len(y) == 1 else 0.0
            else:
                slope = float(y[-1] - y[-2])
                base = float(y[-1])

            for i, dt in enumerate(future_months, start=1):
                rows.append(
                    {
                        "month": dt.strftime("%Y-%m"),
                        "category": category,
                        "forecast_total_spent": round(max(0.0, base + slope * i), 2),
                        "method": method,
                    }
                )

        out = pd.DataFrame(rows).sort_values(["month", "forecast_total_spent"], ascending=[True, False])
        return out

