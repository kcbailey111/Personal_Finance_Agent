"""
Bill / Recurring Charges Agent

Detects recurring transactions (subscriptions, bills) and can produce a simple
"bill calendar" for expected next due dates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BillDetectionConfig:
    min_occurrences: int = 3
    monthly_min_days: int = 25
    monthly_max_days: int = 35
    amount_tolerance: float = 0.15  # +/- 15%


class BillAgent:
    def __init__(self, config: BillDetectionConfig | None = None):
        self.config = config or BillDetectionConfig()

    @staticmethod
    def _prepare(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["amount"] = pd.to_numeric(out.get("amount"), errors="coerce")
        out["date"] = pd.to_datetime(out.get("date"), errors="coerce")
        out = out.dropna(subset=["amount", "date"])
        if "merchant_normalized" not in out.columns:
            merchant = out.get("merchant", out.get("description", "")).astype(str)
            out["merchant_normalized"] = (
                merchant.str.lower().str.replace(r"[^a-z0-9\\s]", "", regex=True).str.replace(r"\\s+", " ", regex=True).str.strip()
            )
        return out

    def mark_recurring(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        df = self._prepare(transactions_df)
        if df.empty:
            return transactions_df.copy()

        out = transactions_df.copy()
        out["is_recurring"] = False
        out["recurring_group"] = ""

        work = df.sort_values(["merchant_normalized", "date"])
        for merchant, mdf in work.groupby("merchant_normalized"):
            if len(mdf) < self.config.min_occurrences:
                continue

            dates = mdf["date"].sort_values().to_list()
            amounts = mdf["amount"].astype(float).to_numpy()

            # Check typical amount consistency
            med = float(np.median(amounts))
            if med == 0:
                continue
            within = np.abs(amounts - med) / abs(med) <= self.config.amount_tolerance
            if within.mean() < 0.6:
                continue

            # Check monthly-like cadence (median gap)
            gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
            if not gaps:
                continue
            gap_med = int(np.median(gaps))
            if not (self.config.monthly_min_days <= gap_med <= self.config.monthly_max_days):
                continue

            idx = mdf.index
            out.loc[idx, "is_recurring"] = True
            out.loc[idx, "recurring_group"] = f"{merchant}:{round(med, 2)}"

            # Add tag if present
            if "tags" in out.columns:
                def _add_tag(t: str) -> str:
                    cur = str(t or "")
                    parts = [p for p in cur.split(",") if p]
                    if "recurring" not in parts:
                        parts.append("recurring")
                    return ",".join(sorted(set(parts)))

                out.loc[idx, "tags"] = out.loc[idx, "tags"].apply(_add_tag)

        return out

    def build_bill_calendar(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        df = self._prepare(transactions_df)
        if df.empty:
            return pd.DataFrame(columns=["merchant", "typical_amount", "typical_day", "last_seen", "next_due"])

        if "is_recurring" in df.columns:
            df = df[df["is_recurring"] == True]  # noqa: E712

        if df.empty:
            return pd.DataFrame(columns=["merchant", "typical_amount", "typical_day", "last_seen", "next_due"])

        rows: list[dict] = []
        for merchant, mdf in df.sort_values("date").groupby("merchant_normalized"):
            amounts = mdf["amount"].astype(float).to_numpy()
            typical_amount = float(np.median(amounts)) if len(amounts) else 0.0
            typical_day = int(np.median(mdf["date"].dt.day))
            last_seen = mdf["date"].max().normalize()
            next_due = (last_seen + pd.Timedelta(days=30)).normalize()
            rows.append(
                {
                    "merchant": merchant,
                    "typical_amount": round(typical_amount, 2),
                    "typical_day": typical_day,
                    "last_seen": last_seen.strftime("%Y-%m-%d"),
                    "next_due": next_due.strftime("%Y-%m-%d"),
                }
            )

        return pd.DataFrame(rows).sort_values(["next_due", "typical_amount"], ascending=[True, False])

