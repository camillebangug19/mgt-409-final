"""Configuration and .env loading.

Per REQUIREMENTS.md 4.2 the .env file is looked for in two places, in order:
  1. the repo root
  2. one level above the repo root
Both paths are resolved from __file__ so the app behaves the same no matter
what the current working directory is.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> app -> backend -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
KB_DIR = BACKEND_DIR / "kb"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

ENV_SEARCH_PATHS = (REPO_ROOT / ".env", REPO_ROOT.parent / ".env")

MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

MISSING_KEY_MESSAGE = (
    "PORTKEY_API_KEY was not found.\n"
    "Looked for a .env file in:\n"
    "  1. {first}\n"
    "  2. {second}\n"
    "Copy .env.example to one of those locations and set PORTKEY_API_KEY."
)


def load_env(search_paths=None) -> Path | None:
    """Load the first .env that exists. Returns the path used, or None."""
    for candidate in search_paths or ENV_SEARCH_PATHS:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return candidate
    return None


def get_portkey_api_key(search_paths=None) -> str:
    """Return the Portkey key, raising a clear error when it is missing.

    The key itself is never logged or included in the error message.
    """
    paths = tuple(search_paths or ENV_SEARCH_PATHS)
    load_env(paths)
    key = os.environ.get("PORTKEY_API_KEY", "").strip()
    if not key:
        first = paths[0] if paths else "(none)"
        second = paths[1] if len(paths) > 1 else "(none)"
        raise RuntimeError(MISSING_KEY_MESSAGE.format(first=first, second=second))
    return key


def db_path() -> Path:
    """Location of the SQLite file (overridable for tests)."""
    return Path(os.environ.get("READYHOME_DB", BACKEND_DIR / "readyhome.db"))
