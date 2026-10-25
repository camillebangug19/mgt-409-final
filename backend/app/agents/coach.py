"""The Coach agent (REQUIREMENTS.md 5.1).

It writes one short "why this matters for you" per candidate step. It cannot
invent steps or links: the candidates come from rank_next_steps, the facts come
from get_guidance, and the verifier removes anything else before display.
"""

from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ..llm import get_model
from ..models import HouseholdProfile
from ..tools.guidance import get_guidance, get_local_resources, quantities_for


class CoachNote(BaseModel):
    step_id: str = Field(description="One of the candidate step ids, copied exactly.")
    why: str = Field(description="One or two sentences on why this matters for THIS household.")


class NextStepsPlan(BaseModel):
    notes: list[CoachNote] = Field(default_factory=list, description="One note per candidate step.")


@dataclass
class CoachDeps:
    profile: HouseholdProfile


SYSTEM_PROMPT = """
You are ReadyHome's coach. You are given steps that have already been chosen
for a household by a scoring system. Your only job is to explain, in one or two
warm plain sentences each, why that step matters for THIS household.

Rules you must not break:
- Write a note for every candidate step you are given, and no others. Copy the
  step_id exactly. Never invent a step.
- Never write a URL. Links are attached separately from the knowledge base.
- Use get_guidance for the facts behind a step. Do not add facts of your own.
- Refer to the household concretely: the baby, the dog, the person who uses
  oxygen, living in an apartment without a car.
- Never give medical advice, dosing, or tell anyone to change a medication.
  For medication steps, point to their doctor or pharmacist.
- No scare tactics. Be encouraging and practical.
""".strip()


def build_coach_agent(model=None) -> Agent[CoachDeps, NextStepsPlan]:
    agent = Agent(
        model or get_model(),
        deps_type=CoachDeps,
        output_type=NextStepsPlan,
        system_prompt=SYSTEM_PROMPT,
        retries=2,
    )

    @agent.tool
    def guidance(ctx: RunContext[CoachDeps], module_id: str) -> dict:
        """Vetted guidance text and sources for a step id."""
        return get_guidance(module_id)

    @agent.tool
    def local_resources(ctx: RunContext[CoachDeps]) -> dict:
        """Verified local resources for this household's state."""
        return get_local_resources(ctx.deps.profile.state)

    @agent.tool
    def quantities(ctx: RunContext[CoachDeps], days: int = 3) -> dict:
        """How much water and food this household needs, and pet counts."""
        return quantities_for(ctx.deps.profile, days)

    return agent


def describe_household(profile: HouseholdProfile) -> str:
    """A compact, privacy-safe description for the prompt. No names, no address."""
    ages: dict[str, int] = {}
    for person in profile.people:
        ages[person.age_group] = ages.get(person.age_group, 0) + 1
    people = ", ".join(f"{count} {group.replace('_', ' ')}" for group, count in ages.items())

    bits = [f"Household: {people or 'unknown'}."]
    needs = []
    for index, person in enumerate(profile.people, start=1):
        detail = []
        if person.mobility != "none":
            detail.append(f"uses a {person.mobility.replace('_', ' ')}")
        if person.needs_evac_help:
            detail.append("needs help evacuating")
        if person.power_equipment:
            detail.append("uses " + ", ".join(person.power_equipment) + " (needs electricity)")
        if person.daily_meds:
            detail.append("takes daily medication")
        if person.infant_feeding:
            detail.append(f"fed by {person.infant_feeding}")
        if detail:
            needs.append(f"person {index} {', '.join(detail)}")
    if needs:
        bits.append("Needs: " + "; ".join(needs) + ".")

    if profile.pets:
        bits.append("Pets: " + ", ".join(f"{p.count} {p.species}" for p in profile.pets) + ".")

    location = []
    if profile.state:
        location.append(f"state {profile.state}")
    if profile.housing_type:
        location.append(profile.housing_type.replace("_", " "))
    if profile.has_vehicle is False:
        location.append("no working vehicle")
    elif profile.has_vehicle:
        location.append("has a vehicle")
    if location:
        bits.append("Location: " + ", ".join(location) + ".")

    return " ".join(bits)


def coach_prompt(profile: HouseholdProfile, candidates: list[dict]) -> str:
    lines = [
        f"- {c['id']}: {c['title']} (worth +{c['points_gain']} points to them)"
        for c in candidates
    ]
    return (
        f"{describe_household(profile)}\n\n"
        "Candidate steps, already chosen for them:\n"
        + "\n".join(lines)
        + "\n\nWrite one note for each candidate step id above."
    )
