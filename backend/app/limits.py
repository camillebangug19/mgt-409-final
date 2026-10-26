"""Cost and loop controls (REQUIREMENTS.md 10).

Three layers:
  1. PydanticAI UsageLimits on every run, so one turn cannot loop forever.
  2. A per-session turn cap, so one visitor cannot run the survey forever.
  3. A global daily token budget in SQLite, so the whole app has a ceiling.
"""

import os

from pydantic_ai.usage import UsageLimits

from .safety import MAX_TURNS

# One turn is a few tool calls and one reply. Anything past this is a loop.
SURVEY_LIMITS = UsageLimits(request_limit=12, tool_calls_limit=20)
COACH_LIMITS = UsageLimits(request_limit=8, tool_calls_limit=12)

DEFAULT_DAILY_TOKEN_BUDGET = 2_000_000

BUDGET_MESSAGE = (
    "ReadyHome has hit its daily limit for today. "
    "Your answers are saved, so please come back tomorrow."
)
TURN_LIMIT_MESSAGE = (
    "We've covered a lot in this conversation! Your answers are saved - "
    "start a new check if you'd like to go again."
)


def daily_token_budget() -> int:
    return int(os.environ.get("READYHOME_DAILY_TOKEN_BUDGET", DEFAULT_DAILY_TOKEN_BUDGET))


def tokens_used_today(conn) -> int:
    row = conn.execute(
        """SELECT COALESCE(SUM(input_tokens + output_tokens), 0) AS total
             FROM usage WHERE day = date('now')"""
    ).fetchone()
    return int(row["total"] or 0)


def budget_exceeded(conn) -> bool:
    return tokens_used_today(conn) >= daily_token_budget()


def turns_used(conn, session_id: str) -> int:
    row = conn.execute(
        "SELECT turn_count FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    return int(row["turn_count"]) if row else 0


def turn_limit_reached(conn, session_id: str) -> bool:
    return turns_used(conn, session_id) >= MAX_TURNS


def record_run_usage(conn, session_id: str, agent: str, usage) -> dict:
    """Store what one agent run cost. Returns the numbers for the cost panel."""
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    cached = int(getattr(usage, "cache_read_tokens", 0) or 0)

    conn.execute(
        """INSERT INTO usage (session_id, agent, input_tokens, cached_tokens, output_tokens)
           VALUES (?, ?, ?, ?, ?)""",
        (session_id, agent, input_tokens, cached, output_tokens),
    )
    return {
        "agent": agent,
        "input_tokens": input_tokens,
        "cached_tokens": cached,
        "output_tokens": output_tokens,
    }
