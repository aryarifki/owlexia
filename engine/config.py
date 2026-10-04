"""Configuration and Environment Settings for OWLEXIA Legal AI Agent."""
import os
from pathlib import Path
from typing import Optional

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def load_env_file(filepath: Optional[Path] = None) -> None:
    """Loads environment variables from a .env file into os.environ if not already present."""
    target = filepath or ENV_FILE
    if not target.exists():
        return

    try:
        with open(target, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


# Automatically load on module import
load_env_file()


def get_gemini_api_key() -> str:
    load_env_file()
    return os.getenv("GEMINI_API_KEY", "")


def get_gemini_model() -> str:
    load_env_file()
    return os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def get_reasoner_mode() -> str:
    load_env_file()
    return os.getenv("REASONER_MODE", "llm").lower()


def get_database_url() -> str:
    load_env_file()
    return os.getenv(
        "DATABASE_URL",
        "postgresql://owlexia:owlexia_pass@localhost:5432/owlexia_db"
    )
