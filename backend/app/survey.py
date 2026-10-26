"""The survey slot engine (REQUIREMENTS.md 5.3).

Plain Python decides which slots exist, which are still missing and what the
next question is about. The LLM only phrases the question and parses the reply
into `record_answer`, so the conversation can never wander off the script.
"""

import json
import re
from typing import Any

from . import kb
from .models import HouseholdProfile, Person, Pet
from .scoring import applicable_items

SECTIONS = ("Household", "Needs", "Pets", "Location", "What you already have")

AGE_GROUPS = ("infant", "child", "teen", "adult", "older_adult")
AGE_GROUP_HINT = "infant (<1), child (1-12), teen, adult, older_adult (65+)"
MOBILITY_OPTIONS = ("none", "cane_or_walker", "wheelchair", "bedbound")
EQUIPMENT_OPTIONS = ("oxygen", "cpap", "dialysis", "powered_wheelchair", "other")
HOUSING_OPTIONS = ("house", "apartment", "mobile_home", "other")
ANSWER_OPTIONS = ("yes", "partly", "no", "not_sure")

# Baseline slots are named after their rubric item, so scoring reads them directly.
BASELINE_PROMPTS = {
    "water": "three or more days of water stored (1 gallon per person per day)",
    "food": "three or more days of food that needs no cooking",
    "light_radio": "a flashlight, a radio and spare batteries",
    "first_aid": "a first-aid kit",
    "phone_power": "a way to charge a phone when the power is out",
    "written_plan": "a written family emergency plan",
    "meeting_place": "an agreed meeting place",
    "out_of_area_contact": "an out-of-area contact everyone knows",
    "knows_routes": "knowing your evacuation routes",
    "transportation_plan": "a transportation plan if you had to leave",
    "alerts_on": "emergency alerts turned on",
    "meds_7day": "a 7-day supply of daily medications",
    "backup_power": "a backup power plan for medical equipment",
    "infant_feeding": "emergency infant feeding supplies",
    "evacuation_helper": "someone arranged to help you evacuate",
    "pet_go_kit": "a go-kit for your pets",
    "pet_lodging": "pet-friendly lodging identified",
}

# Concrete examples, so "do you have three days of food" is answerable.
# These are what the question means, not extra advice.
BASELINE_EXAMPLES = {
    "water": "a gallon per person per day, so a four-person household needs 12 gallons for three days. Stored bottles or refilled clean bottles both count",
    "food": "food that needs no cooking, like tinned beans, tuna, peanut butter, crackers, dried fruit or tinned soup",
    "light_radio": "a torch or flashlight, a battery or hand-crank radio, and spare batteries that fit them",
    "first_aid": "plasters, gauze, tape, antiseptic, gloves and any personal items your household uses",
    "phone_power": "a power bank, a car charger, or a hand-crank charger",
    "written_plan": "one page everyone can find, saying where to meet, who to call, and who does what",
    "meeting_place": "somewhere specific, like the big tree in the park or the library car park",
    "out_of_area_contact": "someone far enough away that they would not be in the same emergency, who everyone knows to ring",
    "knows_routes": "two different ways out of your neighbourhood that you have actually driven or walked",
    "transportation_plan": "who drives, or which bus, train or paratransit service you would use if you had to leave",
    "alerts_on": "Wireless Emergency Alerts on your phone, a county or city alert signup, or a NOAA weather radio",
    "meds_7day": "about a week of each daily medication, plus a written list of what everyone takes",
    "backup_power": "a charged battery, a generator, or a plan for where to go if the power stays off",
    "infant_feeding": "several days of formula or feeding supplies, clean water to prepare it, and a way to clean bottles",
    "evacuation_helper": "a specific person who has agreed to come and help, plus a backup person",
    "pet_go_kit": "pet food and water, a spare leash or carrier, vaccination records and any pet medication",
    "pet_lodging": "somewhere specific outside your area that you have checked takes pets",
}

# Questions about bodies, medication and needing help are asked gently:
# Sunny takes her sunglasses off for these (REQUIREMENTS.md 18.1).
SENSITIVE_SLOTS = frozenset({
    "mobility_needs",
    "power_equipment",
    "daily_meds",
    "infant_feeding_method",
    "meds_7day",
    "backup_power",
    "evacuation_helper",
    "infant_feeding",
})


def is_sensitive(slot: str | None) -> bool:
    """Whether this question deserves the calm face."""
    return slot in SENSITIVE_SLOTS


MAX_PEOPLE = 12

# Which person has a need is a nice-to-have: scoring only asks whether anyone
# does, and build_profile guesses sensibly. Asking costs a turn for nothing.
NO_FOLLOW_UP = (
    " If they say who, record it, but never ask a follow-up just to find out who."
)


class SlotError(ValueError):
    """Raised when a value does not fit the slot's schema."""


# --- validation -----------------------------------------------------------

def _as_obj(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def _one_of(value: Any, options: tuple[str, ...], slot: str) -> str:
    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if text not in options:
        raise SlotError(f"{slot} must be one of {', '.join(options)} (got {value!r})")
    return text


def _as_bool(value: Any, slot: str) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "yes", "y", "1"):
        return True
    if text in ("false", "no", "n", "0"):
        return False
    raise SlotError(f"{slot} must be yes or no (got {value!r})")


def validate_slot(slot: str, value: Any) -> Any:
    """Validate and normalise one answer. Raises SlotError with a usable message."""
    value = _as_obj(value)

    if slot == "num_people":
        try:
            count = int(value)
        except (TypeError, ValueError):
            raise SlotError(f"num_people must be a whole number (got {value!r})")
        if not 1 <= count <= MAX_PEOPLE:
            raise SlotError(f"num_people must be between 1 and {MAX_PEOPLE}")
        return count

    if re.fullmatch(r"person_\d+", slot):
        if isinstance(value, str):
            value = {"age_group": value}
        if not isinstance(value, dict) or "age_group" not in value:
            raise SlotError(f"{slot} needs an age_group: {AGE_GROUP_HINT}")
        person = {"age_group": _one_of(value["age_group"], AGE_GROUPS, slot)}
        nickname = (value.get("nickname") or "").strip()
        if nickname:
            person["nickname"] = nickname[:40]
        return person

    if slot == "mobility_needs":
        if _is_none_marker(value):
            return {"none": True}
        cleaned = []
        for entry in _people_entries(value, slot):
            mobility = entry.get("mobility")
            helps = entry.get("needs_evac_help")
            # A bare answer like "wheelchair" or "needs help evacuating".
            if mobility is None:
                text = str(entry.get("text", "")).lower()
                if "evacuat" in text or "help" in text:
                    mobility, helps = "none", True
                else:
                    mobility = text or "none"
            cleaned.append({
                "person": _person_index(entry, slot),
                "mobility": _one_of(mobility, MOBILITY_OPTIONS, slot),
                "needs_evac_help": _as_bool(helps, slot) if helps is not None else False,
            })
        return {"people": cleaned}

    if slot == "power_equipment":
        if _is_none_marker(value):
            return {"none": True}
        cleaned = []
        for entry in _people_entries(value, slot):
            raw = entry.get("equipment") or entry.get("equipment_list") or entry.get("text") or []
            if isinstance(raw, str):
                raw = [part for part in re.split(r"[,/]| and ", raw) if part.strip()]
            equipment = []
            for item in raw:
                try:
                    equipment.append(_one_of(item, EQUIPMENT_OPTIONS, slot))
                except SlotError:
                    equipment.append("other")  # unrecognised device still counts
            cleaned.append({
                "person": _person_index(entry, slot),
                "equipment": equipment or ["other"],
            })
        return {"people": cleaned}

    if slot == "daily_meds":
        if _is_none_marker(value):
            return {"none": True}
        people = value.get("people") if isinstance(value, dict) else value
        if isinstance(people, (int, str)):
            people = [people]
        if not isinstance(people, list) or not people:
            # "yes" with nobody named still means somebody takes medication.
            return {"people": [None]}
        return {"people": [_person_index({"person": p}, slot) for p in people]}

    if slot == "infant_feeding_method":
        return _one_of(value, ("breast", "formula", "both"), slot)

    if slot == "pets":
        if _is_none_marker(value):
            return {"none": True}
        raw = value.get("pets") if isinstance(value, dict) else value
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list) or not raw:
            raise SlotError("pets needs 'none' or a list of {species, count}")
        pets = []
        for entry in raw:
            if isinstance(entry, str):
                entry = {"species": entry}
            species = str(entry.get("species", "")).strip()[:30]
            if not species:
                raise SlotError("each pet needs a species")
            count = int(entry.get("count", 1) or 1)
            pets.append({"species": species, "count": max(1, min(count, 50))})
        return {"pets": pets}

    if slot == "zip_code":
        text = str(value).strip()
        if not re.fullmatch(r"\d{5}", text):
            raise SlotError("zip_code must be 5 digits")
        return text

    if slot == "state":
        text = str(value).strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", text):
            raise SlotError("state must be a 2-letter abbreviation, e.g. TX")
        return text

    if slot == "housing_type":
        return _one_of(value, HOUSING_OPTIONS, slot)

    if slot == "has_vehicle":
        return _as_bool(value, slot)

    if slot in BASELINE_PROMPTS:
        return _one_of(value, ANSWER_OPTIONS, slot)

    raise SlotError(f"unknown slot {slot!r}")


def _is_none_marker(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(value.get("none"))
    if isinstance(value, list):
        return not value
    text = str(value).strip().lower().rstrip(".!")
    return text in ("none", "no", "nobody", "no one", "n", "false", "[]", "", "no pets", "none of us")


def _people_entries(value: Any, slot: str) -> list[dict]:
    """Accept the structured form, or a plain answer like "oxygen"."""
    if isinstance(value, str):
        return [{"text": value}]
    entries = value.get("people") if isinstance(value, dict) else value
    if entries is None and isinstance(value, dict):
        # e.g. {"equipment": ["oxygen"]} with no person named
        entries = [value]
    if isinstance(entries, dict):
        entries = [entries]
    if not isinstance(entries, list) or not entries:
        raise SlotError(f"{slot} needs 'none' or a list of people")
    return [e if isinstance(e, dict) else {"text": str(e)} for e in entries]


def _person_index(entry: Any, slot: str) -> int | None:
    """Which person this is about, or None when we were not told.

    None is fine: scoring only asks whether anyone in the household has the
    need. build_profile attaches an unattributed need to the most likely
    person so the Coach can still say something concrete.
    """
    raw = entry.get("person", entry.get("index")) if isinstance(entry, dict) else entry
    if raw is None or (isinstance(raw, str) and not raw.strip().isdigit()):
        return None
    try:
        index = int(raw)
    except (TypeError, ValueError):
        return None
    return index if 1 <= index <= MAX_PEOPLE else None


# --- which slots exist, given what we know so far -------------------------

def required_slots(answers: dict[str, Any]) -> list[tuple[str, str]]:
    """Ordered (slot, section) pairs, expanded from the answers so far.

    Conditional slots only appear once the answer that triggers them is in:
    a person slot per household member, infant feeding only with an infant,
    pet questions only with pets, and medical baseline items only when needed.
    """
    slots: list[tuple[str, str]] = [("num_people", "Household")]

    count = answers.get("num_people")
    if not isinstance(count, int):
        # Until we know the household size we cannot know how many person slots
        # there are, so this is the only question that exists yet.
        return slots
    for i in range(1, count + 1):
        slots.append((f"person_{i}", "Household"))

    slots += [
        ("mobility_needs", "Needs"),
        ("power_equipment", "Needs"),
        ("daily_meds", "Needs"),
    ]

    # Infant feeding depends on an age group we may not have been told yet.
    known = [answers.get(f"person_{i}") for i in range(1, count + 1)]
    if any(isinstance(p, dict) and p.get("age_group") == "infant" for p in known):
        slots.append(("infant_feeding_method", "Needs"))

    slots.append(("pets", "Pets"))
    slots += [
        ("zip_code", "Location"),
        ("state", "Location"),
        ("housing_type", "Location"),
        ("has_vehicle", "Location"),
    ]

    # Baseline questions depend on the profile, so only ask once it is known.
    if all(slot in answers for slot, _ in slots):
        profile = build_profile(answers)
        for item in applicable_items(profile):
            slots.append((item["id"], "What you already have"))

    return slots


# Who an unattributed need most likely belongs to, oldest first.
_LIKELIHOOD = ("older_adult", "adult", "teen", "child", "infant")


def _likely_person(answers: dict[str, Any], count: int) -> int:
    """Which person a need belongs to when nobody was named.

    Scoring only cares whether anyone has the need, so this only affects how
    concretely the Coach can describe it. Oldest first is the best guess.
    """
    for age_group in _LIKELIHOOD:
        for i in range(1, count + 1):
            entry = answers.get(f"person_{i}")
            if isinstance(entry, dict) and entry.get("age_group") == age_group:
                return i
    return 1


def _attribute(entries: list[dict], answers: dict[str, Any], count: int) -> dict[int, dict]:
    """Index entries by person, filling in a best guess where none was given."""
    attributed: dict[int, dict] = {}
    for entry in entries:
        index = entry.get("person") or _likely_person(answers, count)
        attributed[index] = entry
    return attributed


def build_profile(answers: dict[str, Any]) -> HouseholdProfile:
    """Assemble a HouseholdProfile from whatever slots are filled."""
    count = int(answers.get("num_people") or 0)
    mobility = _attribute((answers.get("mobility_needs") or {}).get("people", []), answers, count)
    equipment = _attribute((answers.get("power_equipment") or {}).get("people", []), answers, count)
    meds = {
        (p or _likely_person(answers, count))
        for p in (answers.get("daily_meds") or {}).get("people", [])
    }
    feeding = answers.get("infant_feeding_method")

    people = []
    for i in range(1, count + 1):
        entry = answers.get(f"person_{i}")
        if not isinstance(entry, dict):
            continue
        age_group = entry["age_group"]
        people.append(
            Person(
                age_group=age_group,
                nickname=entry.get("nickname"),
                mobility=mobility.get(i, {}).get("mobility", "none"),
                needs_evac_help=mobility.get(i, {}).get("needs_evac_help", False),
                power_equipment=equipment.get(i, {}).get("equipment", []),
                daily_meds=i in meds,
                infant_feeding=feeding if age_group == "infant" else None,
            )
        )

    pets = [Pet(**p) for p in (answers.get("pets") or {}).get("pets", [])]

    return HouseholdProfile(
        people=people,
        pets=pets,
        zip_code=answers.get("zip_code"),
        state=answers.get("state"),
        housing_type=answers.get("housing_type"),
        has_vehicle=answers.get("has_vehicle"),
    )


def baseline_answers(answers: dict[str, Any]) -> dict[str, str]:
    """Just the rubric-item answers, in the shape score_readiness expects."""
    return {k: v for k, v in answers.items() if k in BASELINE_PROMPTS and isinstance(v, str)}


# --- state the agent sees -------------------------------------------------

def question_hint(slot: str, answers: dict[str, Any]) -> str:
    """A short description of what to ask next. The agent does the wording."""
    if slot == "num_people":
        return "how many people live in the household, including them"
    if match := re.fullmatch(r"person_(\d+)", slot):
        n = match.group(1)
        who = "the person answering, so ask about them" if n == "1" else f"person {n}"
        return (
            f"the age group of {who} ({AGE_GROUP_HINT}). "
            "A nickname is optional and they can skip it"
        )
    if slot == "mobility_needs":
        return ("whether anyone uses a cane, walker or wheelchair, is bedbound, "
                "or would need help to evacuate." + NO_FOLLOW_UP)
    if slot == "power_equipment":
        return ("whether anyone uses equipment that needs electricity "
                "(oxygen, CPAP, dialysis, powered wheelchair, other)." + NO_FOLLOW_UP)
    if slot == "daily_meds":
        return "whether anyone takes daily medication." + NO_FOLLOW_UP
    if slot == "infant_feeding_method":
        return "how the infant is fed: breast, formula or both"
    if slot == "pets":
        return "whether they have pets, and if so what kind and how many"
    if slot == "zip_code":
        return "their 5-digit ZIP code (no street address)"
    if slot == "state":
        return "their state, as a 2-letter abbreviation"
    if slot == "housing_type":
        return "whether they live in a house, apartment, mobile home or something else"
    if slot == "has_vehicle":
        return "whether they have a working vehicle available"
    if slot in BASELINE_PROMPTS:
        example = BASELINE_EXAMPLES.get(slot)
        hint = f"whether they already have {BASELINE_PROMPTS[slot]}"
        if example:
            hint += (
                f". Say briefly what that means in practice: {example}. "
                "Keep the whole question under about 35 words"
            )
        return hint + ". Answer yes, partly, no or not sure"
    return f"the value for {slot}"


# Short, friendly versions of each question, for when the bot has to redirect
# someone. question_hint() is written for the model and must never be shown to
# a user: it contains the internal slot vocabulary.
SHORT_QUESTIONS = {
    "num_people": "how many people live in your home, including you?",
    "mobility_needs": "does anyone use a cane, walker or wheelchair, or need a hand getting out?",
    "power_equipment": "does anyone use equipment that needs electricity?",
    "daily_meds": "does anyone take medication every day?",
    "infant_feeding_method": "how is the baby fed?",
    "pets": "do you have any pets?",
    "zip_code": "what is your ZIP code?",
    "state": "which state are you in?",
    "housing_type": "do you live in a house, apartment or mobile home?",
    "has_vehicle": "do you have a working vehicle?",
}


def short_question(slot: str | None) -> str:
    """A friendly one-line version of the current question."""
    if not slot:
        return "how ready your household is"
    if slot in SHORT_QUESTIONS:
        return SHORT_QUESTIONS[slot]
    if re.fullmatch(r"person_\d+", slot):
        number = slot.split("_")[1]
        return (
            "what age group are you in?"
            if number == "1"
            else f"what age group is person {number}?"
        )
    if slot in BASELINE_PROMPTS:
        return f"do you already have {BASELINE_PROMPTS[slot]}?"
    return "how ready your household is"


def quick_replies_for(slot: str) -> list[str]:
    if slot == "num_people":
        return ["1", "2", "3", "4", "5+"]
    if re.fullmatch(r"person_\d+", slot):
        return ["Infant (under 1)", "Child (1-12)", "Teen", "Adult", "Older adult (65+)"]
    if slot == "mobility_needs":
        return ["No one", "Cane or walker", "Wheelchair", "Needs help evacuating"]
    if slot == "power_equipment":
        return ["No one", "Oxygen", "CPAP", "Dialysis", "Powered wheelchair"]
    if slot == "daily_meds":
        return ["No one", "Yes, one person", "Yes, more than one"]
    if slot == "infant_feeding_method":
        return ["Breast", "Formula", "Both"]
    if slot == "pets":
        return ["No pets", "Dog", "Cat", "Other"]
    if slot == "housing_type":
        return ["House", "Apartment", "Mobile home", "Other"]
    if slot == "has_vehicle":
        return ["Yes", "No"]
    if slot in BASELINE_PROMPTS:
        return ["Yes", "Partly", "No", "Not sure"]
    return []


def is_askable(slot: str, answers: dict[str, Any]) -> bool:
    """Whether this slot is one of the questions the survey currently has.

    Stops answers landing out of order, e.g. a baseline question being
    recorded before we know whether it even applies to this household.
    """
    return slot in {name for name, _ in required_slots(answers)}


def survey_state(answers: dict[str, Any]) -> dict:
    """What is filled, what is missing, and what to ask next."""
    required = required_slots(answers)
    filled = [slot for slot, _ in required if slot in answers]
    missing = [(slot, section) for slot, section in required if slot not in answers]

    next_slot, next_section = (missing[0] if missing else (None, None))
    done = not missing and bool(answers.get("num_people"))

    return {
        "filled": filled,
        "missing": [slot for slot, _ in missing],
        "next_slot": next_slot,
        "next_section": next_section,
        "next_question_about": question_hint(next_slot, answers) if next_slot else None,
        "quick_replies": quick_replies_for(next_slot) if next_slot else [],
        "sections": list(SECTIONS),
        "section_index": SECTIONS.index(next_section) if next_section else len(SECTIONS) - 1,
        "progress": round(len(filled) / max(len(required), 1), 2),
        "done": done,
    }
