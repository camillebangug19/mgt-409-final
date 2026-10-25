"""A scripted stand-in for gpt-6-luna, so tests never hit the network."""

import json
import re

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

# What a cooperative user would answer for each slot (persona A shaped).
SCRIPTED_ANSWERS = {
    "num_people": 4,
    "person_1": {"age_group": "adult"},
    "person_2": {"age_group": "adult"},
    "person_3": {"age_group": "infant"},
    "person_4": {"age_group": "child"},
    "mobility_needs": "none",
    "power_equipment": "none",
    "daily_meds": "none",
    "infant_feeding_method": "formula",
    "pets": [{"species": "dog", "count": 1}],
    "zip_code": "78701",
    "state": "TX",
    "housing_type": "house",
    "has_vehicle": "yes",
    # Baseline, matching persona A: water Yes, food Partly, alerts Yes, rest No.
    "water": "yes",
    "food": "partly",
    "alerts_on": "yes",
}
DEFAULT_BASELINE = "no"


def _current_turn(messages: list[ModelMessage]) -> tuple[str, list[ModelMessage]]:
    """The latest user prompt, and everything the model has done since it.

    History accumulates across turns, so anything earlier belongs to a turn
    that is already finished and must not be counted again.
    """
    start = 0
    prompt = ""
    for index, message in enumerate(messages):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                    prompt, start = part.content, index
    return prompt, messages[start:]


def scripted_survey_model(answers: dict | None = None) -> FunctionModel:
    """Records the slot the prompt asks for, then returns a SurveyTurn.

    It mirrors what the real agent does — one record_answer call, then the
    structured output — without any model involved.
    """
    script = {**SCRIPTED_ANSWERS, **(answers or {})}

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompt, this_turn = _current_turn(messages)
        already_recorded = any(
            isinstance(part, ToolCallPart) and part.tool_name == "record_answer"
            for message in this_turn
            if isinstance(message, ModelResponse)
            for part in message.parts
        )
        match = re.search(r"Next slot to fill: (\S+)", prompt)

        # First pass for this turn: record the answer to the slot being asked.
        if match and not already_recorded:
            slot = match.group(1)
            value = script.get(slot, DEFAULT_BASELINE)
            # The real model can only send strings, so the stub does the same.
            if not isinstance(value, str):
                value = json.dumps(value)
            return ModelResponse(parts=[ToolCallPart("record_answer", {"slot": slot, "value": value})])

        done = "Every slot is filled" in prompt or not match
        return ModelResponse(
            parts=[
                ToolCallPart(
                    "final_result",
                    {
                        "message": "Thanks, that is everything." if done else "Got it. Next question.",
                        "quick_replies": [],
                        "done": done,
                    },
                )
            ]
        )

    return FunctionModel(respond)


def scripted_coach_model(invent: bool = False) -> FunctionModel:
    """Stands in for the Coach. With invent=True it misbehaves, for the verifier."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompt, _ = _current_turn(messages)
        step_ids = re.findall(r"^- ([a-z0-9-]+):", prompt, flags=re.MULTILINE)

        notes = [{"step_id": sid, "why": f"This matters for your household ({sid})."} for sid in step_ids]
        if invent:
            notes.append({"step_id": "buy-a-bunker", "why": "See https://totally-fake.example.com"})

        return ModelResponse(parts=[ToolCallPart("final_result", {"notes": notes})])

    return FunctionModel(respond)
