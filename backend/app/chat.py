"""Runs one survey turn: load state, call the agent, persist what it recorded."""

import json
from typing import Any

from pydantic_ai.messages import ModelMessage

from . import db, survey
from .agents.survey_bot import SurveyDeps, build_survey_agent, user_prompt
from .api_models import ChatResponse

# Message history per session, kept in memory. Restarting the server only
# costs conversational context; the answers themselves live in SQLite.
_HISTORY: dict[str, list[ModelMessage]] = {}

_agent = None


def get_agent(model=None):
    """The survey agent, built once. Pass a model to override it in tests."""
    global _agent
    if model is not None:
        return build_survey_agent(model)
    if _agent is None:
        _agent = build_survey_agent()
    return _agent


def load_answers(conn, session_id: str) -> dict[str, Any]:
    """Answers come back out of SQLite as JSON."""
    raw = db.load_answers(conn, session_id)
    return {slot: json.loads(value) for slot, value in raw.items()}


def save_answers(conn, session_id: str, answers: dict[str, Any], slots: list[str]) -> None:
    for slot in slots:
        if slot in answers:
            db.save_answer(conn, session_id, slot, json.dumps(answers[slot]))


def to_response(message: str, quick_replies: list[str], state: dict, done: bool) -> ChatResponse:
    total = len(state["filled"]) + len(state["missing"])
    return ChatResponse(
        message=message,
        quick_replies=quick_replies or state["quick_replies"],
        done=done,
        next_slot=state["next_slot"],
        section=state["next_section"] or survey.SECTIONS[-1],
        sections=state["sections"],
        section_index=state["section_index"],
        progress=state["progress"],
        filled=len(state["filled"]),
        total=total,
    )


async def run_turn(conn, session_id: str, message: str, model=None) -> ChatResponse:
    """One user message in, one bot turn out."""
    answers = load_answers(conn, session_id)
    state = survey.survey_state(answers)

    deps = SurveyDeps(answers=dict(answers))
    agent = get_agent(model)

    result = await agent.run(
        user_prompt(message, state),
        deps=deps,
        message_history=_HISTORY.get(session_id),
    )
    _HISTORY[session_id] = result.all_messages()

    save_answers(conn, session_id, deps.answers, deps.recorded)

    new_state = survey.survey_state(deps.answers)
    done = new_state["done"]
    if done and not db.get_session(conn, session_id)["survey_done"]:
        conn.execute("UPDATE sessions SET survey_done = 1 WHERE session_id = ?", (session_id,))
        db.log_event(conn, session_id, "survey_completed")

    conn.execute(
        "UPDATE sessions SET turn_count = turn_count + 1 WHERE session_id = ?", (session_id,)
    )
    db.save_profile(conn, session_id, survey.build_profile(deps.answers).model_dump())

    return to_response(result.output.message, result.output.quick_replies, new_state, done)


def reset_history(session_id: str | None = None) -> None:
    if session_id is None:
        _HISTORY.clear()
    else:
        _HISTORY.pop(session_id, None)
