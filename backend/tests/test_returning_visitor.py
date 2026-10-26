"""Remembering a visitor without accounts (REQUIREMENTS.md 6.4, 9)."""

import pytest
from fastapi.testclient import TestClient

from app import chat, survey
from app.agents.survey_bot import build_survey_agent
from app.main import app
from stub_model import scripted_survey_model


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("READYHOME_DB", str(tmp_path / "test.db"))
    monkeypatch.setattr(chat, "_agent", build_survey_agent(scripted_survey_model()))
    chat.reset_history()
    with TestClient(app) as test_client:
        yield test_client


def test_an_unknown_id_is_simply_not_found(client):
    assert client.get("/api/session/nope").json() == {"found": False}


def test_a_part_finished_session_reports_where_it_got_to(client):
    session_id = client.post("/api/session").json()["session_id"]
    client.post("/api/chat", json={"session_id": session_id, "message": "hi"})

    status = client.get(f"/api/session/{session_id}").json()
    assert status["found"] is True
    assert status["survey_done"] is False
    assert 0 < status["progress"] < 1
    assert status["answered"] >= 1


def test_a_finished_session_reports_the_score_and_household(client):
    session_id = client.post("/api/session").json()["session_id"]
    turn = client.post("/api/chat", json={"session_id": session_id, "message": "hi"}).json()
    while not turn["done"]:
        turn = client.post("/api/chat", json={"session_id": session_id, "message": "ok"}).json()
    client.get("/api/plan", params={"session_id": session_id})

    status = client.get(f"/api/session/{session_id}").json()
    assert status["survey_done"] is True
    assert status["progress"] == 1.0
    assert status["latest_score"] == 3.0
    assert status["people"] == 4
    assert status["pets"] == 1
    assert status["state"] == "TX"


def test_the_status_never_leaks_personal_detail(client):
    """Counts and a state, never names, nicknames or free text."""
    session_id = client.post("/api/session").json()["session_id"]
    client.post("/api/chat", json={"session_id": session_id, "message": "I am Camille at 12 Oak St"})

    body = client.get(f"/api/session/{session_id}").text
    assert "Camille" not in body and "Oak" not in body


def test_the_chat_tells_the_ui_which_slot_is_being_asked(client):
    """So it can show the state picker instead of a free-text box."""
    session_id = client.post("/api/session").json()["session_id"]
    turn = client.post("/api/chat", json={"session_id": session_id, "message": ""}).json()
    # next_slot is what the bot is asking about now, after recording this turn.
    assert turn["next_slot"] in {name for name, _ in survey.required_slots({"num_people": 4})}

    seen = {turn["next_slot"]}
    while not turn["done"]:
        turn = client.post("/api/chat", json={"session_id": session_id, "message": "ok"}).json()
        seen.add(turn["next_slot"])
    assert "state" in seen, "the UI needs to know when to show the state picker"
    assert turn["next_slot"] is None


# --- the questions explain themselves ------------------------------------

def test_every_baseline_question_carries_a_concrete_example():
    for slot in survey.BASELINE_PROMPTS:
        assert slot in survey.BASELINE_EXAMPLES, f"{slot} has no example"
        hint = survey.question_hint(slot, {})
        assert survey.BASELINE_EXAMPLES[slot] in hint


def test_the_food_question_names_actual_foods():
    hint = survey.question_hint("food", {})
    assert "no cooking" in hint
    for food in ("tinned beans", "peanut butter", "crackers"):
        assert food in hint


def test_examples_do_not_smuggle_in_medical_dosing():
    from app.verifier import contains_dosing

    for slot, example in survey.BASELINE_EXAMPLES.items():
        assert not contains_dosing(example), slot
