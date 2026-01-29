"""
AI Visualization Tool (MVP, offline)

Generates a simple standalone HTML dashboard with:
- top categories table
- monthly totals table
- a tiny inline SVG bar chart for top categories

No external JS/CDN dependencies (works offline).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tools.expense_stats import ExpenseAnalytics


@dataclass(frozen=True)
class DashboardConfig:
    top_n: int = 8


class AIVisualizationTool:
    def __init__(self, config: DashboardConfig | None = None):
        self.config = config or DashboardConfig()

    @staticmethod
    def _escape(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    @staticmethod
    def _df_to_html_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "<p><em>No data</em></p>"
        return df.to_html(index=False, border=0, classes="table")

    @staticmethod
    def _svg_bar(categories: pd.DataFrame) -> str:
        if categories.empty:
            return ""
        maxv = float(categories["total_spent"].max()) if "total_spent" in categories.columns else 0.0
        maxv = max(maxv, 1e-9)
        width = 640
        bar_h = 18
        gap = 6
        height = len(categories) * (bar_h + gap) + 10
        y = 10
        bars = []
        for _, row in categories.iterrows():
            label = str(row.get("category", ""))
            val = float(row.get("total_spent", 0.0))
            w = int((val / maxv) * (width - 220))
            bars.append(
                f'<text x="0" y="{y+14}" font-size="12" fill="#222">{label}</text>'
                f'<rect x="210" y="{y}" width="{w}" height="{bar_h}" fill="#4f46e5" rx="3" />'
                f'<text x="{210+w+8}" y="{y+14}" font-size="12" fill="#222">${val:,.2f}</text>'
            )
            y += bar_h + gap
        return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">' + "".join(bars) + "</svg>"

    def generate_smart_dashboard(self, transactions_df: pd.DataFrame, output_path: Path) -> Path:
        analytics = ExpenseAnalytics(transactions_df)
        top = analytics.get_category_summary().head(self.config.top_n)
        monthly = analytics.get_monthly_summary()

        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Personal Finance Dashboard</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; color: #111; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
    h1 {{ margin: 0 0 12px; font-size: 22px; }}
    h2 {{ margin: 0 0 12px; font-size: 16px; }}
    .table {{ border-collapse: collapse; width: 100%; }}
    .table th, .table td {{ padding: 8px 10px; border-bottom: 1px solid #eee; text-align: left; }}
    .muted {{ color: #6b7280; font-size: 12px; }}
  </style>
</head>
<body>
  <h1>Personal Finance Dashboard</h1>
  <p class="muted">Generated locally (offline-friendly).</p>

  <div class="card">
    <h2>Top categories</h2>
    {self._svg_bar(top)}
    {self._df_to_html_table(top)}
  </div>

  <div class="card">
    <h2>Monthly totals</h2>
    {self._df_to_html_table(monthly)}
  </div>
</body>
</html>
"""
        output_path.write_text(html, encoding="utf-8")
        return output_path

