import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


# If the key is missing, the app should still run in non-LLM mode.
LLM_ENABLED = _env_flag("LLM_ENABLED", default=bool(OPENAI_API_KEY))

# Default models (can be overridden per-agent if needed)
OPENAI_CATEGORIZATION_MODEL = os.getenv("OPENAI_CATEGORIZATION_MODEL", "gpt-5-mini")
OPENAI_INSIGHTS_MODEL = os.getenv("OPENAI_INSIGHTS_MODEL", "gpt-5-mini")
