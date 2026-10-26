"""Request and response shapes for the HTTP API."""

from pydantic import BaseModel, Field

from .agents.survey_bot import MAX_MESSAGE_CHARS


class SessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(default="", max_length=MAX_MESSAGE_CHARS)


class CompleteStepRequest(BaseModel):
    session_id: str
    checked: list[str] = Field(default_factory=list, description="Self-check item ids ticked.")


class ChatResponse(BaseModel):
    message: str
    quick_replies: list[str] = []
    done: bool = False
    # Lets the UI show the right control, e.g. the state picker.
    next_slot: str | None = None
    # Which Sunny face to show beside this message.
    mood: str = "hi"
    # Set when the pre-filter redirected this message.
    flagged: bool = False
    # After repeated off-topic turns the UI offers chips only.
    chips_only: bool = False
    section: str | None = None
    sections: list[str] = []
    section_index: int = 0
    progress: float = 0.0
    filled: int = 0
    total: int = 0
