"""The four events the north-star metric is built from (REQUIREMENTS.md 6.4)."""

from . import db

SURVEY_STARTED = "survey_started"
SURVEY_COMPLETED = "survey_completed"
SCORE_SHOWN = "score_shown"
STEP_COMPLETED = "step_completed"

ALL_EVENTS = (SURVEY_STARTED, SURVEY_COMPLETED, SCORE_SHOWN, STEP_COMPLETED)


def log(conn, session_id: str, name: str, payload: dict | None = None) -> None:
    """Record one event. Unknown names are rejected so the metrics stay clean."""
    if name not in ALL_EVENTS:
        raise ValueError(f"unknown event {name!r}; expected one of {ALL_EVENTS}")
    db.log_event(conn, session_id, name, payload)


def counts(conn) -> dict[str, int]:
    rows = conn.execute("SELECT name, COUNT(*) AS n FROM events GROUP BY name")
    found = {r["name"]: r["n"] for r in rows}
    return {name: found.get(name, 0) for name in ALL_EVENTS}
