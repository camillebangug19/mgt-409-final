"""Pydantic models for the household profile, survey answers and results."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

AgeGroup = Literal["infant", "child", "teen", "adult", "older_adult"]
Mobility = Literal["none", "cane_or_walker", "wheelchair", "bedbound"]
PowerEquipment = Literal["oxygen", "cpap", "dialysis", "powered_wheelchair", "other"]
InfantFeeding = Literal["breast", "formula", "both"]
HousingType = Literal["house", "apartment", "mobile_home", "other"]

# Yes = full credit, Partly = half, No / Not sure = none (REQUIREMENTS.md 5.3)
AnswerValue = Literal["yes", "partly", "no", "not_sure"]
ANSWER_CREDIT: dict[str, float] = {"yes": 1.0, "partly": 0.5, "no": 0.0, "not_sure": 0.0}


class Person(BaseModel):
    age_group: AgeGroup
    nickname: str | None = None
    mobility: Mobility = "none"
    needs_evac_help: bool = False
    power_equipment: list[PowerEquipment] = Field(default_factory=list)
    daily_meds: bool = False
    infant_feeding: InfantFeeding | None = None


class Pet(BaseModel):
    species: str
    count: int = Field(default=1, ge=1, le=50)


class HouseholdProfile(BaseModel):
    people: list[Person] = Field(default_factory=list)
    pets: list[Pet] = Field(default_factory=list)
    zip_code: str | None = None
    state: str | None = None
    housing_type: HousingType | None = None
    has_vehicle: bool | None = None

    @field_validator("state")
    @classmethod
    def _upper_state(cls, v: str | None) -> str | None:
        return v.upper() if v else v

    # --- derived flags, used by rubric `applies_if` -----------------------
    @property
    def has_infant(self) -> bool:
        return any(p.age_group == "infant" for p in self.people)

    @property
    def has_meds(self) -> bool:
        return any(p.daily_meds for p in self.people)

    @property
    def has_power_dependent(self) -> bool:
        return any(p.power_equipment for p in self.people)

    @property
    def needs_evac_help(self) -> bool:
        return any(
            p.needs_evac_help or p.mobility in ("wheelchair", "bedbound")
            for p in self.people
        )

    @property
    def has_pets(self) -> bool:
        return any(p.count > 0 for p in self.pets)

    @property
    def has_no_vehicle(self) -> bool:
        return self.has_vehicle is False

    def flags(self) -> dict[str, bool]:
        return {
            "always": True,
            "has_infant": self.has_infant,
            "has_meds": self.has_meds,
            "has_power_dependent": self.has_power_dependent,
            "needs_evac_help": self.needs_evac_help,
            "has_pets": self.has_pets,
            "has_no_vehicle": self.has_no_vehicle,
        }


class CategoryBreakdown(BaseModel):
    category: str
    earned: float
    max_points: float


class ScoreResult(BaseModel):
    score: float
    label: str
    earned: float
    max_points: float
    breakdown: list[CategoryBreakdown]
    missing_item_ids: list[str]
    applicable_item_ids: list[str]


class NextStep(BaseModel):
    id: str
    title: str
    points_gain: float
    est_minutes: int
    est_cost_band: str
    how_to: list[str]
    self_check: list[dict]
    source_ids: list[str]
    cheap_option_ids: list[str]
    why: str = ""
