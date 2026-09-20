"""Configuration — reads .env if present, no external dependencies."""

from __future__ import annotations

import os

_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")


def _load_env() -> None:
    if os.path.exists(_ENV_PATH):
        with open(_ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

LLM_ENABLED = bool(GEMINI_API_KEY)
