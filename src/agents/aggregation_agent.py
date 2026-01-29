"""
Multi-Account Aggregation Agent (MVP)

Combines multiple CSV transaction files into a single DataFrame with a `source`
column. This keeps things local and avoids external integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class AggregationConfig:
    source_column: str = "source"


class AggregationAgent:
    def __init__(self, config: AggregationConfig | None = None):
        self.config = config or AggregationConfig()

    def aggregate_csvs(self, csv_paths: list[Path]) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for p in csv_paths:
            try:
                df = pd.read_csv(p)
                df[self.config.source_column] = p.stem
                frames.append(df)
            except Exception:
                continue
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

