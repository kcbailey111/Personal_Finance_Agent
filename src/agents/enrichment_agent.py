"""
Transaction Enrichment & Tagging Agent

Adds extra metadata fields to each transaction:
- tags (comma-separated)
- expense_type (subscription|bill|purchase|transfer|income|unknown)
- merchant_type (best-effort heuristic)

Designed to work fully offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class EnrichmentConfig:
    subscription_keywords: tuple[str, ...] = (
        "netflix",
        "spotify",
        "hulu",
        "prime",
        "apple",
        "google",
        "microsoft",
        "adobe",
        "gym",
        "membership",
        "subscription",
    )


class EnrichmentAgent:
    def __init__(self, config: EnrichmentConfig | None = None):
        self.config = config or EnrichmentConfig()

    @staticmethod
    def _norm(s: object) -> str:
        return str(s or "").strip().lower()

    def _classify_expense_type(self, row: pd.Series) -> str:
        category = self._norm(row.get("category"))
        desc = self._norm(row.get("description"))
        merchant = self._norm(row.get("merchant"))

        if category == "income" or desc.startswith("payroll") or "salary" in desc:
            return "income"
        if category == "transfer" or "transfer" in desc:
            return "transfer"
        if any(k in desc or k in merchant for k in self.config.subscription_keywords):
            return "subscription"
        if "utility" in category or any(k in desc for k in ("electric", "water", "internet", "phone")):
            return "bill"
        return "purchase"

    @staticmethod
    def _merchant_type(desc: str, merchant: str) -> str:
        s = f"{desc} {merchant}".lower()
        rules = [
            ("grocery", ("whole foods", "costco", "kroger", "walmart", "aldi", "trader joe", "grocery")),
            ("ride_share", ("uber", "lyft")),
            ("travel", ("airbnb", "delta", "united", "hotel", "marriott", "hilton")),
            ("coffee", ("starbucks", "coffee")),
            ("streaming", ("netflix", "spotify", "hulu", "disney")),
            ("retail", ("amazon", "target", "best buy", "apple store")),
            ("dining", ("restaurant", "mcdonald", "chipotle", "cafe", "dining")),
            ("utilities", ("comcast", "verizon", "at&t", "electric", "water", "gas")),
        ]
        for label, keys in rules:
            if any(k in s for k in keys):
                return label
        return "unknown"

    def enrich_dataframe(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        df = transactions_df.copy()
        if df.empty:
            return df

        if "description" not in df.columns:
            df["description"] = ""
        if "merchant" not in df.columns:
            # fall back to description as a best-effort "merchant"
            df["merchant"] = df["description"].astype(str).str.split().str[:2].str.join(" ")

        # expense_type
        df["expense_type"] = df.apply(self._classify_expense_type, axis=1)

        # tags
        tags = []
        for _, row in df.iterrows():
            row_tags: list[str] = []
            et = str(row.get("expense_type") or "")
            if et in {"subscription", "bill"}:
                row_tags.append("recurring_candidate")
            if et == "income":
                row_tags.append("income")
            if et == "transfer":
                row_tags.append("transfer")

            # crude tax tag heuristic
            if self._norm(row.get("category")) in {"utilities", "rent"}:
                row_tags.append("essential")
            if self._norm(row.get("category")) in {"shopping", "entertainment", "dining"}:
                row_tags.append("discretionary")

            tags.append(",".join(sorted(set(row_tags))))

        df["tags"] = tags

        # merchant_type
        df["merchant_type"] = [
            self._merchant_type(str(d), str(m)) for d, m in zip(df["description"].astype(str), df["merchant"].astype(str))
        ]

        # normalize merchant (strip noise)
        df["merchant_normalized"] = (
            df["merchant"].astype(str).str.lower().str.replace(r"[^a-z0-9\\s]", "", regex=True).str.strip()
        )
        df["merchant_normalized"] = df["merchant_normalized"].str.replace(r"\\s+", " ", regex=True)
        df["merchant_normalized"] = df["merchant_normalized"].str.replace(r"\\b(inc|llc|co|corp)\\b", "", regex=True).str.strip()

        # best-effort recurring merchant hint based on description tokens
        df["recurring_hint"] = df["tags"].astype(str).str.contains("recurring_candidate", na=False)

        # optional: extract a likely subscription/bill name
        def _sub_name(row: pd.Series) -> str:
            if not str(row.get("recurring_hint")):
                return ""
            txt = f"{row.get('merchant_normalized','')} {row.get('description','')}".lower()
            m = re.search(r"(netflix|spotify|hulu|disney|prime|comcast|verizon|att|at&t|apple|google|adobe)", txt)
            return (m.group(1) if m else row.get("merchant_normalized", ""))[:50]

        df["recurring_name"] = df.apply(_sub_name, axis=1)

        return df

