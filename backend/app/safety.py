"""Input defences for the chat (REQUIREMENTS.md 10).

The real protection is structural: the bot can only change state through
record_answer, which is schema-validated, and the verifier only lets through
knowledge-base steps and links. This module adds the cheap checks in front:
a length cap, a prompt-injection pre-filter, and an off-topic counter.
"""

import re

MAX_MESSAGE_CHARS = 500

# MAX_TURNS counts turns that actually reached the model. A large household
# needs 33 questions, so counting redirects against this budget could cut a
# real survey off before it finished.
MAX_TURNS = 40

# Redirects get their own ceiling so someone cannot sit here forever.
MAX_OFFTOPIC = 12

# After this many nudges the UI stops offering a free-text box.
OFFTOPIC_LIMIT = 3

# Phrases that try to talk to the model rather than answer the question.
INJECTION_PATTERNS = (
    r"ignore (all |any |the )?(previous|prior|above|earlier)",
    r"disregard (all |any |the )?(previous|prior|above|earlier|instructions)",
    r"forget (everything|all|your|the) (you|instructions|rules|prompt)",
    r"\b(system|developer) (prompt|message|instructions?)\b",
    r"(reveal|show|print|repeat|output|tell me) (me )?(your|the) (system |initial |original )?(prompt|instructions|rules)",
    r"you are (now|no longer)\b",
    r"\bact as\b|\bpretend to be\b|\broleplay as\b",
    r"\bnew instructions?\b|\boverride\b",
    r"\bjailbreak\b|\bDAN mode\b",
    r"</?(system|assistant|user)>",
    r"\[/?(INST|SYS)\]",
    r"\bprompt injection\b",
    r"repeat (everything |all )?(above|the text above)",
    # No \b around these: underscores are word characters, so \bapi_key\b
    # never fires inside "PORTKEY_API_KEY".
    r"api[_ -]?key|portkey|secret[_ -]?key|environment variable|\.env\b",
)

# Clearly nothing to do with household preparedness.
OFFTOPIC_PATTERNS = (
    r"\bwrite (me )?(a |an )?(poem|song|essay|story|code|script|program)\b",
    r"\b(translate|summari[sz]e) (this|the following)\b",
    r"\bwhat('| i)s the (weather|capital|time) (in|of)\b",
    r"\bwho (is|was) (the )?(president|prime minister)\b",
    r"\b(solve|calculate|what is) \d+\s*[-+*/x]\s*\d+",
    r"\brecipe for\b",
    r"\btell me a joke\b",
)

REDIRECT = (
    "I can only help with getting your household ready for an emergency, "
    "but I'm happy to keep going with that! "
)
INJECTION_REDIRECT = (
    "I'll stick to the readiness questions. "
    "Anything you type here I treat as information about your household. "
)


def _matches(text: str, patterns: tuple[str, ...]) -> str | None:
    lowered = (text or "").lower()
    for pattern in patterns:
        if re.search(pattern, lowered):
            return pattern
    return None


def clamp(message: str) -> str:
    """Hard length cap, applied before the text reaches the model."""
    return (message or "")[:MAX_MESSAGE_CHARS]


def looks_like_injection(message: str) -> bool:
    return _matches(message, INJECTION_PATTERNS) is not None


def looks_off_topic(message: str) -> bool:
    return _matches(message, OFFTOPIC_PATTERNS) is not None


class Screening:
    """What the pre-filter decided about one message."""

    def __init__(self, message: str, injection: bool, off_topic: bool, pattern: str | None):
        self.message = message
        self.injection = injection
        self.off_topic = off_topic
        self.pattern = pattern

    @property
    def flagged(self) -> bool:
        return self.injection or self.off_topic

    @property
    def note(self) -> str:
        if self.injection:
            return INJECTION_REDIRECT
        if self.off_topic:
            return REDIRECT
        return ""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Screening(injection={self.injection}, off_topic={self.off_topic})"


def screen(message: str) -> Screening:
    """Cap the length and check for injection or off-topic chatter."""
    text = clamp(message)
    injection_hit = _matches(text, INJECTION_PATTERNS)
    off_topic_hit = None if injection_hit else _matches(text, OFFTOPIC_PATTERNS)
    return Screening(
        message=text,
        injection=injection_hit is not None,
        off_topic=off_topic_hit is not None,
        pattern=injection_hit or off_topic_hit,
    )
