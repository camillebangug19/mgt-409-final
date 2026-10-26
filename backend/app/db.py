"""SQLite storage: anonymous sessions, answers, completions, events, usage.

One file, no accounts (REQUIREMENTS.md 4 / 6.4). Only a ZIP and state are
stored for location; no names are required and no street address is collected.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import db_path

__all__ = ["db_path", "connect", "init_db", "session_db"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    profile_json TEXT NOT NULL DEFAULT '{}',
    turn_count   INTEGER NOT NULL DEFAULT 0,
    offtopic_count INTEGER NOT NULL DEFAULT 0,
    survey_done  INTEGER NOT NULL DEFAULT 0,
    first_score  REAL,
    latest_score REAL
);

CREATE TABLE IF NOT EXISTS answers (
    session_id TEXT NOT NULL,
    slot       TEXT NOT NULL,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (session_id, slot)
);

CREATE TABLE IF NOT EXISTS step_completions (
    session_id   TEXT NOT NULL,
    step_id      TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (session_id, step_id)
);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    name       TEXT NOT NULL,
    payload    TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS usage (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL,
    agent         TEXT NOT NULL,
    input_tokens  INTEGER NOT NULL DEFAULT 0,
    cached_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    day           TEXT NOT NULL DEFAULT (date('now')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = Path(path or db_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | None = None) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def session_db(path: Path | None = None):
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- sessions -------------------------------------------------------------

def create_session(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (session_id,))


def get_session(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()


def save_profile(conn: sqlite3.Connection, session_id: str, profile: dict) -> None:
    conn.execute(
        "UPDATE sessions SET profile_json = ? WHERE session_id = ?",
        (json.dumps(profile), session_id),
    )


def load_profile(conn: sqlite3.Connection, session_id: str) -> dict:
    row = get_session(conn, session_id)
    return json.loads(row["profile_json"]) if row else {}


def record_score(conn: sqlite3.Connection, session_id: str, score: float) -> None:
    conn.execute(
        """UPDATE sessions
              SET latest_score = ?,
                  first_score = COALESCE(first_score, ?)
            WHERE session_id = ?""",
        (score, score, session_id),
    )


# --- answers and completions ---------------------------------------------

def save_answer(conn: sqlite3.Connection, session_id: str, slot: str, value: str) -> None:
    conn.execute(
        """INSERT INTO answers (session_id, slot, value) VALUES (?, ?, ?)
           ON CONFLICT(session_id, slot)
           DO UPDATE SET value = excluded.value, updated_at = datetime('now')""",
        (session_id, slot, value),
    )


def load_answers(conn: sqlite3.Connection, session_id: str) -> dict[str, str]:
    rows = conn.execute("SELECT slot, value FROM answers WHERE session_id = ?", (session_id,))
    return {r["slot"]: r["value"] for r in rows}


def complete_step(conn: sqlite3.Connection, session_id: str, step_id: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO step_completions (session_id, step_id) VALUES (?, ?)",
        (session_id, step_id),
    )


def completed_steps(conn: sqlite3.Connection, session_id: str) -> set[str]:
    rows = conn.execute("SELECT step_id FROM step_completions WHERE session_id = ?", (session_id,))
    return {r["step_id"] for r in rows}


# --- events and usage -----------------------------------------------------

def log_event(conn: sqlite3.Connection, session_id: str, name: str, payload: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO events (session_id, name, payload) VALUES (?, ?, ?)",
        (session_id, name, json.dumps(payload or {})),
    )


def log_usage(conn, session_id: str, agent: str, input_tokens: int, cached_tokens: int, output_tokens: int) -> None:
    conn.execute(
        """INSERT INTO usage (session_id, agent, input_tokens, cached_tokens, output_tokens)
           VALUES (?, ?, ?, ?, ?)""",
        (session_id, agent, input_tokens, cached_tokens, output_tokens),
    )
