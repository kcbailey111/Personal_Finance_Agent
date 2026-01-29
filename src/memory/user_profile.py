"""
User Profile (MVP)

Stores optional user preferences used by agents (budgets, income, goals).
This is intentionally lightweight and file-based.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class UserProfile:
    user_id: str = "default"
    monthly_income: float | None = None
    preferences: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["preferences"] = d["preferences"] or {}
        return d

    @classmethod
    def load(cls, path: Path) -> "UserProfile":
        try:
            raw = path.read_text(encoding="utf-8").strip()
            if not raw:
                return cls()
            data = json.loads(raw)
            return cls(
                user_id=str(data.get("user_id", "default")),
                monthly_income=float(data["monthly_income"]) if data.get("monthly_income") is not None else None,
                preferences=data.get("preferences") if isinstance(data.get("preferences"), dict) else {},
            )
        except Exception:
            return cls()

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

