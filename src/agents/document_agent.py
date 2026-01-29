"""
Receipt / Document Analysis Agent (Scaffold)

Full receipt OCR + parsing typically requires:
- a vision model (OpenAI vision) and/or OCR (tesseract, cloud vision)
- image/PDF dependencies (Pillow, pdfplumber, etc.)

This file provides a clean extension point without breaking the current app.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DocumentAgentConfig:
    pass


class DocumentAgent:
    def __init__(self, config: DocumentAgentConfig | None = None):
        self.config = config or DocumentAgentConfig()

    def parse_receipt(self, file_path: Path) -> dict[str, Any]:
        raise NotImplementedError(
            "Receipt parsing is scaffolded but not implemented yet. "
            "If you want, I can add OpenAI vision parsing (images) and PDF parsing next."
        )

