"""The landing copy is used exactly as written (REQUIREMENTS.md 18.2).

Reads the spec and the frontend copy file and compares them, so a reworded
headline fails here rather than quietly shipping.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "REQUIREMENTS.md"
COPY = REPO_ROOT / "frontend" / "src" / "copy" / "landing.ts"


@pytest.fixture(scope="module")
def spec_section() -> str:
    text = SPEC.read_text(encoding="utf-8")
    start = text.index("### 18.2")
    return text[start : text.index("### 18.3", start)]


@pytest.fixture(scope="module")
def copy_text() -> str:
    return COPY.read_text(encoding="utf-8")


def _spec_value(section: str, label: str) -> str:
    """Pull one '- **Label:** value' line out of the spec."""
    match = re.search(rf"^- \*\*{re.escape(label)}:\*\* (.+)$", section, re.MULTILINE)
    assert match, f"{label} not found in REQUIREMENTS 18.2"
    return match.group(1).strip()


def _normalise(text: str) -> str:
    """Compare wording, not quote style or escaping."""
    text = text.replace("\\'", "'").replace('\\"', '"')
    for fancy, plain in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"')):
        text = text.replace(fancy, plain)
    return re.sub(r"\s+", " ", text).strip()


@pytest.mark.parametrize(
    "label",
    ["Eyebrow", "Headline", "Subhead", "Button", "Under button", "Closing line", "Footer"],
)
def test_each_labelled_line_appears_verbatim(spec_section, copy_text, label):
    expected = _normalise(_spec_value(spec_section, label))
    assert expected in _normalise(copy_text), f"{label} does not match the spec"


def test_the_three_tiles_are_present(spec_section, copy_text):
    tiles = _spec_value(spec_section, "Tiles")
    # "3 easy minutes: just tap or type" - split on the quoted segments.
    for quoted in re.findall(r'"([^"]+)"', tiles):
        big, _, cap = quoted.partition(": ")
        assert _normalise(big) in _normalise(copy_text), big
        assert _normalise(cap) in _normalise(copy_text), cap


def test_the_three_how_it_works_steps_are_present(spec_section, copy_text):
    steps = re.findall(r"^\s+\d\. \*\*(.+?)\*\* (.+)$", spec_section, re.MULTILINE)
    assert len(steps) == 3, "expected three how-it-works steps in the spec"
    body = _normalise(copy_text)
    for lead, rest in steps:
        assert _normalise(lead) in body, lead
        assert _normalise(rest) in body, rest


def test_the_landing_component_renders_the_copy_file():
    """Catches the copy file being bypassed with inline strings."""
    component = (REPO_ROOT / "frontend" / "src" / "components" / "Landing.tsx").read_text()
    assert "LANDING" in component
    for key in ("headline", "subhead", "button", "closing", "footer", "eyebrow"):
        assert f"LANDING.{key}" in component, key
