"""The survey running end to end through the HTTP API, with a stubbed model."""

import pytest
from fastapi.testclient import TestClient

from app import chat, db
from app.agents.survey_bot import build_survey_agent
from app.main import app
from stub_model import SCRIPTED_ANSWERS, scripted_survey_model


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A client backed by a throwaway database and the scripted model."""
    monkeypatch.setenv("READYHOME_DB", str(tmp_path / "test.db"))
    monkeypatch.setattr(chat, "_agent", build_survey_agent(scripted_survey_model()))
    chat.reset_history()
    with TestClient(app) as test_client:
        yield test_client


def start(client) -> str:
    return client.post("/api/session").json()["session_id"]


def say(client, session_id: str, message: str) -> dict:
    response = client.post("/api/chat", json={"session_id": session_id, "message": message})
    assert response.status_code == 200, response.text
    return response.json()


def test_starting_a_session_logs_the_event(client, tmp_path):
    session_id = start(client)
    assert session_id

    with db.session_db() as conn:
        names = [r["name"] for r in conn.execute("SELECT name FROM events WHERE session_id = ?", (session_id,))]
    assert "survey_started" in names


def test_chat_rejects_an_unknown_session(client):
    response = client.post("/api/chat", json={"session_id": "nope", "message": "hi"})
    assert response.status_code == 404


def test_messages_over_500_characters_are_rejected(client):
    session_id = start(client)
    response = client.post("/api/chat", json={"session_id": session_id, "message": "x" * 501})
    assert response.status_code == 422


def test_the_first_turn_asks_about_the_household(client):
    session_id = start(client)
    turn = say(client, session_id, "")
    assert turn["section"] == "Household"
    assert turn["done"] is False
    assert turn["total"] > 0


def test_a_whole_survey_runs_to_done_and_persists_every_answer(client):
    session_id = start(client)

    turn = say(client, session_id, "hello")
    turns = 1
    while not turn["done"] and turns < 60:
        turn = say(client, session_id, "my answer")
        turns += 1

    assert turn["done"], f"survey did not finish in {turns} turns"
    assert turn["progress"] == 1.0

    with db.session_db() as conn:
        stored = chat.load_answers(conn, session_id)
        session = db.get_session(conn, session_id)
        events = [r["name"] for r in conn.execute("SELECT name FROM events WHERE session_id = ?", (session_id,))]

    # Everything the script answered made it into SQLite.
    for slot, value in SCRIPTED_ANSWERS.items():
        assert slot in stored, f"{slot} was never stored"
    assert stored["zip_code"] == "78701"
    assert stored["state"] == "TX"

    assert session["survey_done"] == 1
    assert session["turn_count"] == turns
    assert "survey_completed" in events


def test_the_survey_finishes_within_the_turn_budget(client):
    """REQUIREMENTS.md 10 caps a session at 40 turns, so it has to fit."""
    session_id = start(client)
    turn = say(client, session_id, "hi")
    turns = 1
    while not turn["done"] and turns < 60:
        turn = say(client, session_id, "ok")
        turns += 1
    assert turns <= 40, f"took {turns} turns, over the 40-turn cap"


def test_the_profile_is_saved_for_scoring(client):
    session_id = start(client)
    turn = say(client, session_id, "hi")
    while not turn["done"]:
        turn = say(client, session_id, "ok")

    with db.session_db() as conn:
        profile = db.load_profile(conn, session_id)
    assert len(profile["people"]) == 4
    assert profile["state"] == "TX"


def test_no_street_address_is_ever_stored(client):
    """REQUIREMENTS.md 9 — ZIP and state only."""
    session_id = start(client)
    turn = say(client, session_id, "I live at 123 Main Street, Austin")
    while not turn["done"]:
        turn = say(client, session_id, "ok")

    with db.session_db() as conn:
        stored = chat.load_answers(conn, session_id)
    assert "123 Main Street" not in str(stored)
    assert set(stored) <= set(SCRIPTED_ANSWERS) | set(__import__("app.survey", fromlist=["x"]).BASELINE_PROMPTS)
