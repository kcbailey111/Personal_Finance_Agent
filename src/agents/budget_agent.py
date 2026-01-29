"""
Budget Agent

- Load budgets from YAML (if available)
- Generate a "smart budget" from historical spending (offline)
- Compare actual spending vs budget to produce alerts
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class BudgetConfig:
    lookback_months: int = 3
    discretionary_categories: tuple[str, ...] = ("Dining", "Entertainment", "Shopping")
    discretionary_target_multiplier: float = 0.90
    essentials_target_multiplier: float = 1.05


class BudgetAgent:
    def __init__(self, config: BudgetConfig | None = None):
        self.config = config or BudgetConfig()

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any] | None:
        try:
            import yaml  # type: ignore
        except Exception:
            return None

        try:
            raw = path.read_text(encoding="utf-8").strip()
            if not raw:
                return None
            parsed = yaml.safe_load(raw)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def load_budget_rules(self, path: Path) -> dict[str, float] | None:
        """
        Expected YAML format:

        budgets:
          Groceries: 400
          Dining: 150
        """
        parsed = self._load_yaml(path)
        if not parsed:
            return None
        budgets = parsed.get("budgets")
        if not isinstance(budgets, dict):
            return None
        out: dict[str, float] = {}
        for k, v in budgets.items():
            try:
                out[str(k)] = float(v)
            except Exception:
                continue
        return out or None

    def generate_smart_budget(self, transactions_df: pd.DataFrame) -> dict[str, Any]:
        df = transactions_df.copy()
        df["amount"] = pd.to_numeric(df.get("amount"), errors="coerce")
        df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
        df = df.dropna(subset=["amount", "date"])
        if df.empty:
            return {"budgets": {}, "method": "empty"}
        if "category" not in df.columns:
            df["category"] = "Uncategorized"

        df["year_month"] = df["date"].dt.to_period("M").dt.to_timestamp()
        # lookback window
        last_month = df["year_month"].max()
        window_start = (last_month - pd.offsets.MonthBegin(self.config.lookback_months)).normalize()
        window = df[df["year_month"] >= window_start]
        if window.empty:
            window = df

        monthly_by_cat = (
            window.groupby(["category", "year_month"], as_index=False)
            .agg(total_spent=("amount", "sum"))
            .sort_values(["category", "year_month"])
        )
        avg_by_cat = monthly_by_cat.groupby("category", as_index=False).agg(avg_monthly=("total_spent", "mean"))

        budgets: dict[str, float] = {}
        for _, row in avg_by_cat.iterrows():
            cat = str(row["category"])
            avg = float(row["avg_monthly"])
            if cat in self.config.discretionary_categories:
                budgets[cat] = round(max(0.0, avg * self.config.discretionary_target_multiplier), 2)
            else:
                budgets[cat] = round(max(0.0, avg * self.config.essentials_target_multiplier), 2)

        return {
            "budgets": budgets,
            "method": "avg_monthly_lookback",
            "lookback_months": self.config.lookback_months,
        }

    def budget_status(self, transactions_df: pd.DataFrame, budgets: dict[str, float]) -> dict[str, Any]:
        df = transactions_df.copy()
        df["amount"] = pd.to_numeric(df.get("amount"), errors="coerce")
        df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
        df = df.dropna(subset=["amount", "date"])
        if df.empty:
            return {"categories": [], "overall": {"total_spent": 0.0, "total_budget": 0.0, "over_budget": False}}
        if "category" not in df.columns:
            df["category"] = "Uncategorized"

        df["year_month"] = df["date"].dt.strftime("%Y-%m")
        current_month = df["year_month"].max()
        cur = df[df["year_month"] == current_month]

        spent_by_cat = cur.groupby("category", as_index=False).agg(spent=("amount", "sum"))
        cats: list[dict[str, Any]] = []

        total_spent = 0.0
        total_budget = 0.0

        for _, row in spent_by_cat.iterrows():
            cat = str(row["category"])
            spent = float(row["spent"])
            budget = float(budgets.get(cat, 0.0))
            cats.append(
                {
                    "category": cat,
                    "month": current_month,
                    "spent": round(spent, 2),
                    "budget": round(budget, 2),
                    "remaining": round(budget - spent, 2),
                    "over_budget": spent > budget if budget > 0 else False,
                }
            )
            total_spent += spent
            total_budget += budget

        cats.sort(key=lambda x: (x["over_budget"], x["spent"]), reverse=True)
        return {
            "categories": cats,
            "overall": {
                "month": current_month,
                "total_spent": round(total_spent, 2),
                "total_budget": round(total_budget, 2),
                "over_budget": total_budget > 0 and total_spent > total_budget,
            },
        }

