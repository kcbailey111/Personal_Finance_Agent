"""
Conversational Financial Assistant (CLI-friendly)

This agent answers common finance questions using deterministic parsing.
If LLM is enabled, it can attempt a best-effort natural-language answer
for unrecognized questions.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from config.settings import LLM_ENABLED, OPENAI_API_KEY, OPENAI_INSIGHTS_MODEL


@dataclass(frozen=True)
class ChatAnswer:
    answer: str
    data_preview: str | None = None


class ChatAgent:
    def __init__(self, enabled: bool | None = None):
        self.enabled = LLM_ENABLED if enabled is None else bool(enabled)
        self._client = None
        if self.enabled and OPENAI_API_KEY:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception:
                self._client = None

    @staticmethod
    def _prepare(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["amount"] = pd.to_numeric(out.get("amount"), errors="coerce")
        out["date"] = pd.to_datetime(out.get("date"), errors="coerce")
        out = out.dropna(subset=["amount", "date"])
        if "category" not in out.columns:
            out["category"] = "Uncategorized"
        out["year_month"] = out["date"].dt.strftime("%Y-%m")
        return out

    @staticmethod
    def _md_table(df: pd.DataFrame, max_rows: int = 15) -> str:
        if df.empty:
            return ""
        head = df.head(max_rows)
        try:
            return head.to_markdown(index=False)
        except Exception:
            # Avoid requiring optional deps (like tabulate)
            return head.to_string(index=False)

    def _answer_rule_based(self, question: str, df: pd.DataFrame) -> ChatAnswer | None:
        q = question.strip().lower()

        # biggest category
        if "biggest" in q and "category" in q:
            by_cat = df.groupby("category", as_index=False).agg(total=("amount", "sum")).sort_values("total", ascending=False)
            if by_cat.empty:
                return ChatAnswer("I don't have enough data to compute that yet.")
            top = by_cat.iloc[0]
            return ChatAnswer(f"Your biggest expense category is **{top['category']}** at **${float(top['total']):,.2f}**.")

        # how much spent on category last month / this month / YYYY-MM
        m = re.search(r"spend on ([a-z\s]+?)(?: last month| this month| in (\d{4}-\d{2}))\??$", q)
        if m:
            cat = m.group(1).strip().title()
            ym = m.group(2)
            if ym:
                target = ym
            else:
                last = df["year_month"].max()
                if "last month" in q:
                    y, mo = map(int, last.split("-"))
                    mo -= 1
                    if mo == 0:
                        y -= 1
                        mo = 12
                    target = f"{y:04d}-{mo:02d}"
                else:
                    target = last
            sub = df[(df["category"].astype(str) == cat) & (df["year_month"] == target)]
            total = float(sub["amount"].sum()) if not sub.empty else 0.0
            return ChatAnswer(f"You spent **${total:,.2f}** on **{cat}** in **{target}**.")

        # show transactions over $X (optional month)
        m = re.search(r"transactions over \$?(\d+(?:\.\d+)?)", q)
        if m:
            thresh = float(m.group(1))
            sub = df[df["amount"] >= thresh].sort_values("amount", ascending=False)
            return ChatAnswer(
                f"Here are transactions over **${thresh:,.2f}** ({len(sub)} found).",
                data_preview=self._md_table(sub[["date", "description", "amount", "category"]], max_rows=20),
            )

        # compare this month vs last month
        if "compare" in q and "this month" in q and "last month" in q:
            last = df["year_month"].max()
            y, mo = map(int, last.split("-"))
            prev_y, prev_m = y, mo - 1
            if prev_m == 0:
                prev_y -= 1
                prev_m = 12
            prev = f"{prev_y:04d}-{prev_m:02d}"
            cur_total = float(df[df["year_month"] == last]["amount"].sum())
            prev_total = float(df[df["year_month"] == prev]["amount"].sum())
            delta = cur_total - prev_total
            pct = (delta / prev_total * 100.0) if prev_total > 0 else 0.0
            return ChatAnswer(
                f"**{last}**: ${cur_total:,.2f}\n\n**{prev}**: ${prev_total:,.2f}\n\nChange: ${delta:,.2f} ({pct:+.1f}%)."
            )

        return None

    def query(self, user_question: str, transactions_df: pd.DataFrame) -> ChatAnswer:
        df = self._prepare(transactions_df)
        if df.empty:
            return ChatAnswer("I don't see any valid transactions (missing/invalid dates or amounts).")

        rb = self._answer_rule_based(user_question, df)
        if rb is not None:
            return rb

        if self._client is None:
            return ChatAnswer(
                "I couldn't parse that question with the built-in rules. "
                "Try something like: 'compare this month vs last month' or 'transactions over $100'."
            )

        # Best-effort LLM answer using compact stats (avoid sending full raw data).
        try:
            by_cat = (
                df.groupby("category", as_index=False).agg(total=("amount", "sum")).sort_values("total", ascending=False).head(8)
            )
            by_month = df.groupby("year_month", as_index=False).agg(total=("amount", "sum")).sort_values("year_month")
            stats = {
                "months": by_month.to_dict(orient="records"),
                "top_categories": by_cat.to_dict(orient="records"),
                "sample_transactions": df[["date", "description", "amount", "category"]].sort_values("date").tail(10).to_dict(
                    orient="records"
                ),
            }
            prompt = (
                "Answer the user's question about their finances using ONLY the provided JSON stats. "
                "Be specific and include numbers.\n\n"
                f"Question: {user_question}\n\nStats JSON:\n{json.dumps(stats, indent=2)}"
            )
            resp = self._client.chat.completions.create(
                model=OPENAI_INSIGHTS_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            answer = (resp.choices[0].message.content or "").strip()
            return ChatAnswer(answer or "I couldn't generate an answer.")
        except Exception:
            return ChatAnswer("I couldn't answer that right now (LLM error).")

