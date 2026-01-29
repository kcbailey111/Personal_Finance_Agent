"""
Goal Tracking Agent (MVP)

Supports simple goals stored as JSON, e.g.:
- reduce_category_spend: {category: "Dining", percent: 30, month: "2026-02"}

This is intentionally minimal; it gives you a clear place to grow coaching logic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class GoalAgentConfig:
    # Placeholder for future knobs
    pass


class GoalAgent:
    def __init__(self, config: GoalAgentConfig | None = None):
        self.config = config or GoalAgentConfig()

    def load_goals(self, path: Path) -> list[dict[str, Any]]:
        try:
            raw = path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save_goals(self, path: Path, goals: list[dict[str, Any]]) -> None:
        path.write_text(json.dumps(goals, indent=2), encoding="utf-8")

    def evaluate_goals(self, transactions_df: pd.DataFrame, goals: list[dict[str, Any]]) -> dict[str, Any]:
        df = transactions_df.copy()
        df["amount"] = pd.to_numeric(df.get("amount"), errors="coerce")
        df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
        df = df.dropna(subset=["amount", "date"])
        if df.empty or not goals:
            return {"goals": [], "summary": "No goals or no data."}
        if "category" not in df.columns:
            df["category"] = "Uncategorized"

        df["year_month"] = df["date"].dt.strftime("%Y-%m")
        latest = df["year_month"].max()

        results: list[dict[str, Any]] = []
        for g in goals:
            gtype = str(g.get("type", ""))
            if gtype == "reduce_category_spend":
                cat = str(g.get("category", ""))
                pct = float(g.get("percent", 0))
                month = str(g.get("month", latest))
                spent = float(df[(df["year_month"] == month) & (df["category"] == cat)]["amount"].sum())
                results.append(
                    {
                        "type": gtype,
                        "category": cat,
                        "month": month,
                        "target_percent": pct,
                        "current_spent": round(spent, 2),
                        "note": "Define a baseline month to compute progress (MVP placeholder).",
                    }
                )
            else:
                results.append({"type": gtype, "status": "unsupported_goal_type"})

        return {"goals": results, "summary": f"Evaluated {len(results)} goal(s)."}

