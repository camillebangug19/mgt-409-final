"""Runs one survey turn: load state, call the agent, persist what it recorded."""

import json
import os
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelRequest, UserPromptPart

from . import db, events, limits, safety, survey
from .agents.survey_bot import SurveyDeps, build_survey_agent, user_prompt
from .api_models import ChatResponse

# Message history per session, kept in memory. Restarting the server only
# costs conversational context; the answers themselves live in SQLite.
_HISTORY: dict[str, list[ModelMessage]] = {}

# Resending the whole conversation every turn makes input tokens grow with the
# square of the turn count: a 24-turn survey measured 647k input tokens. The
# survey state is reloaded from SQLite each turn anyway, so history is only
# needed so Sunny can refer back to what was just said. Keeping the last few
# exchanges is enough for that.
HISTORY_TURNS = int(os.environ.get("READYHOME_HISTORY_TURNS", "4"))


def trim_history(messages: list[ModelMessage] | None, turns: int = HISTORY_TURNS):
    """Keep only the last `turns` user exchanges, cut on turn boundaries.

    Slicing mid-turn would orphan a tool call from its result, so the cut is
    always made at a user prompt.
    """
    if not messages:
        return messages

    boundaries = [
        index
        for index, message in enumerate(messages)
        if isinstance(message, ModelRequest)
        and any(isinstance(part, UserPromptPart) for part in message.parts)
    ]
    if len(boundaries) <= turns:
        return messages
    return messages[boundaries[-turns] :]

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


def mood_for(state: dict, done: bool, suggested: str) -> str:
    """Sunny's face for this message.

    The model proposes a mood, but sensitive questions are forced to "calm"
    here rather than trusted to the prompt (REQUIREMENTS.md 18.1). Mood is
    presentation only and never touches scoring.
    """
    if done:
        return "cheer"
    if survey.is_sensitive(state.get("next_slot")):
        return "calm"
    return suggested if suggested in ("hi", "thinking", "cheer", "calm") else "hi"


def to_response(
    message: str, quick_replies: list[str], state: dict, done: bool, mood: str = "hi"
) -> ChatResponse:
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
        mood=mood_for(state, done, mood),
    )


class BudgetExceeded(Exception):
    """The global daily token budget is gone. Surfaced as a 429."""


async def run_turn(conn, session_id: str, message: str, model=None) -> ChatResponse:
    """One user message in, one bot turn out."""
    if limits.budget_exceeded(conn):
        raise BudgetExceeded(limits.BUDGET_MESSAGE)

    answers = load_answers(conn, session_id)
    state = survey.survey_state(answers)

    # The turn cap stops a session looping forever (REQUIREMENTS.md 10).
    if limits.turn_limit_reached(conn, session_id):
        return to_response(limits.TURN_LIMIT_MESSAGE, [], state, state["done"], "calm")

    # Cheap checks before we pay for a model call.
    screening = safety.screen(message)
    if screening.flagged:
        conn.execute(
            "UPDATE sessions SET offtopic_count = offtopic_count + 1 WHERE session_id = ?",
            (session_id,),
        )
        conn.execute(
            "UPDATE sessions SET turn_count = turn_count + 1 WHERE session_id = ?",
            (session_id,),
        )
        row = db.get_session(conn, session_id)
        nudges = int(row["offtopic_count"]) if row else 1
        reply = screening.note + f"So, {survey.short_question(state['next_slot'])}"
        # After three nudges stop offering a free-text box (REQUIREMENTS.md 10).
        quick = state["quick_replies"] if nudges >= safety.OFFTOPIC_LIMIT else []
        response = to_response(reply, quick, state, False, "calm")
        response.chips_only = nudges >= safety.OFFTOPIC_LIMIT
        response.flagged = True
        return response

    deps = SurveyDeps(answers=dict(answers))
    agent = get_agent(model)

    result = await agent.run(
        user_prompt(screening.message, state),
        deps=deps,
        message_history=trim_history(_HISTORY.get(session_id)),
        usage_limits=limits.SURVEY_LIMITS,
    )
    _HISTORY[session_id] = result.all_messages()
    limits.record_run_usage(conn, session_id, "survey_bot", result.usage)

    save_answers(conn, session_id, deps.answers, deps.recorded)

    new_state = survey.survey_state(deps.answers)
    done = new_state["done"]
    if done and not db.get_session(conn, session_id)["survey_done"]:
        conn.execute("UPDATE sessions SET survey_done = 1 WHERE session_id = ?", (session_id,))
        events.log(conn, session_id, events.SURVEY_COMPLETED)

    conn.execute(
        "UPDATE sessions SET turn_count = turn_count + 1 WHERE session_id = ?", (session_id,)
    )
    db.save_profile(conn, session_id, survey.build_profile(deps.answers).model_dump())

    return to_response(
        result.output.message,
        result.output.quick_replies,
        new_state,
        done,
        result.output.mood,
    )


def reset_history(session_id: str | None = None) -> None:
    if session_id is None:
        _HISTORY.clear()
    else:
        _HISTORY.pop(session_id, None)
