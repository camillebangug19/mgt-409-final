"""REQUIREMENTS.md 13.2 #8 — start, answer, score, complete a step, score up, events."""

import pytest
from fastapi.testclient import TestClient

from app import chat, db, kb, plan
from app.agents.coach import build_coach_agent
from app.agents.survey_bot import build_survey_agent
from app.main import app
from stub_model import scripted_coach_model, scripted_survey_model


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("READYHOME_DB", str(tmp_path / "test.db"))
    monkeypatch.setattr(chat, "_agent", build_survey_agent(scripted_survey_model()))
    monkeypatch.setattr(plan, "_coach", build_coach_agent(scripted_coach_model()))
    chat.reset_history()
    plan.reset_notes()
    with TestClient(app) as test_client:
        yield test_client


def finish_survey(client) -> str:
    session_id = client.post("/api/session").json()["session_id"]
    turn = client.post("/api/chat", json={"session_id": session_id, "message": "hi"}).json()
    guard = 0
    while not turn["done"] and guard < 60:
        turn = client.post("/api/chat", json={"session_id": session_id, "message": "ok"}).json()
        guard += 1
    assert turn["done"]
    return session_id


def get_plan(client, session_id: str) -> dict:
    response = client.get("/api/plan", params={"session_id": session_id})
    assert response.status_code == 200, response.text
    return response.json()


# --- the full journey ------------------------------------------------------

def test_start_answer_score_complete_score_up_events_written(client):
    session_id = finish_survey(client)

    first = get_plan(client, session_id)
    assert first["score"] == 3.0, "the scripted persona A household"
    assert first["label"] == "Just starting"
    assert len(first["steps"]) == 3

    step = first["steps"][0]
    checked = [item["item_id"] for item in step["self_check"]]

    response = client.post(
        f"/api/steps/{step['id']}/complete",
        json={"session_id": session_id, "checked": checked},
    )
    assert response.status_code == 200, response.text
    after = response.json()

    assert after["completion"]["score_after"] > after["completion"]["score_before"]
    assert after["score"] > first["score"]
    assert step["id"] in after["completed_step_ids"]
    assert step["id"] not in {s["id"] for s in after["steps"]}

    with db.session_db() as conn:
        events = [r["name"] for r in conn.execute(
            "SELECT name FROM events WHERE session_id = ? ORDER BY id", (session_id,))]
        session = db.get_session(conn, session_id)

    assert "survey_started" in events
    assert "survey_completed" in events
    assert "score_shown" in events
    assert "step_completed" in events
    assert session["first_score"] == 3.0
    assert session["latest_score"] == after["score"]


def test_the_advertised_points_gain_is_what_actually_happens(client):
    """The '+X points' badge must not lie."""
    session_id = finish_survey(client)
    first = get_plan(client, session_id)
    step = first["steps"][0]

    after = client.post(
        f"/api/steps/{step['id']}/complete",
        json={"session_id": session_id, "checked": [i["item_id"] for i in step["self_check"]]},
    ).json()

    assert after["completion"]["delta"] == step["points_gain"]


def test_a_partly_completed_step_credits_only_what_was_ticked(client):
    """The kit is built in phases, so ticking one box must not credit all five."""
    session_id = finish_survey(client)
    first = get_plan(client, session_id)
    kit = next(s for s in first["steps"] if s["id"] == "kit-phases")

    one_item = [kit["self_check"][0]["item_id"]]
    after = client.post(
        f"/api/steps/kit-phases/complete",
        json={"session_id": session_id, "checked": one_item},
    ).json()

    assert after["completion"]["credited"] == one_item
    assert "kit-phases" not in after["completed_step_ids"], "still has items left"
    assert "kit-phases" in {s["id"] for s in after["steps"]}, "comes back with less to gain"


def test_working_through_every_step_reaches_ten(client):
    session_id = finish_survey(client)
    current = get_plan(client, session_id)
    previous = current["score"]
    guard = 0

    while current["steps"] and guard < 20:
        step = current["steps"][0]
        current = client.post(
            f"/api/steps/{step['id']}/complete",
            json={"session_id": session_id, "checked": [i["item_id"] for i in step["self_check"]]},
        ).json()
        assert current["score"] >= previous, "a completed step never lowers the score"
        previous = current["score"]
        guard += 1

    assert current["score"] == 10.0
    assert current["label"] == "Ready to go!"
    assert current["steps"] == []


def test_never_more_than_three_steps(client):
    session_id = finish_survey(client)
    current = get_plan(client, session_id)
    guard = 0
    while current["steps"] and guard < 20:
        assert len(current["steps"]) <= 3
        step = current["steps"][0]
        current = client.post(
            f"/api/steps/{step['id']}/complete",
            json={"session_id": session_id, "checked": [i["item_id"] for i in step["self_check"]]},
        ).json()
        guard += 1


# --- what the plan contains -------------------------------------------------

def test_every_step_has_a_why_and_real_sources(client):
    session_id = finish_survey(client)
    for step in get_plan(client, session_id)["steps"]:
        assert step["why"].strip()
        assert step["sources"]
        for source in step["sources"]:
            assert kb.source(source["id"]), source
            assert source["source_url"].startswith("https://")


def test_the_plan_carries_the_disclaimer_and_rubric_note(client):
    session_id = finish_survey(client)
    result = get_plan(client, session_id)
    assert "Not medical advice" in result["disclaimer"]
    assert "weights are ReadyHome's own" in result["rubric_note"]


def test_texas_household_gets_the_stear_registry_only_when_relevant(client):
    """Persona A is in TX but nobody needs evacuation help."""
    session_id = finish_survey(client)
    result = get_plan(client, session_id)
    source_ids = {s["id"] for step in result["steps"] for s in step["sources"]}
    assert "tx_stear" not in source_ids


def test_local_resources_only_ever_show_verified_links(client):
    session_id = finish_survey(client)
    for resource in get_plan(client, session_id)["local_resources"]["resources"]:
        assert resource["verified"] and resource["url"] != "TODO"


def test_quantities_match_the_household(client):
    session_id = finish_survey(client)
    quantities = get_plan(client, session_id)["quantities"]
    assert quantities["people"] == 4
    assert quantities["water_gallons"] == 12  # 4 people x 3 days x 1 gallon
    assert quantities["pets"] == 1


# --- the verifier in the real pipeline ---------------------------------------

def test_an_inventing_coach_cannot_reach_the_user(client, monkeypatch):
    monkeypatch.setattr(plan, "_coach", build_coach_agent(scripted_coach_model(invent=True)))
    plan.reset_notes()

    session_id = finish_survey(client)
    result = get_plan(client, session_id)

    assert "buy-a-bunker" not in {s["id"] for s in result["steps"]}
    assert not any("totally-fake" in s["why"] for s in result["steps"])
    assert any("buy-a-bunker" in message for message in result["flagged"])


def test_the_app_still_works_when_the_coach_fails(client, monkeypatch):
    """A Coach outage must not take the score reveal down with it."""
    class Broken:
        async def run(self, *args, **kwargs):
            raise RuntimeError("model unavailable")

    monkeypatch.setattr(plan, "_coach", Broken())
    plan.reset_notes()

    session_id = finish_survey(client)
    result = get_plan(client, session_id)

    assert len(result["steps"]) == 3
    assert all(step["why"].strip() for step in result["steps"]), "falls back to KB wording"
    assert any("coach unavailable" in message for message in result["flagged"])


# --- errors -------------------------------------------------------------------

def test_plan_for_an_unknown_session_is_404(client):
    assert client.get("/api/plan", params={"session_id": "nope"}).status_code == 404


def test_completing_an_unknown_step_is_404(client):
    session_id = finish_survey(client)
    response = client.post(
        "/api/steps/not-a-step/complete", json={"session_id": session_id, "checked": []}
    )
    assert response.status_code == 404
