"""Shared content for report.html and slides.html.

Numbers here come from docs/tokenomics.json (measured by scripts/measure_cost.py)
and from the test suite. Nothing is typed in by hand. Anything not yet measured
is a FILL placeholder, which the build script will list for you.
"""

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "report_assets"

FILL = "[FILL]"

# --- links -----------------------------------------------------------------
REPO_URL = "https://github.com/camillebangug19/mgt-409-final"
LIVE_URL = FILL        # TODO(camille): Render URL, or leave if running locally

AUTHOR = "Camille Bangug"
COURSE = "MGT 409 · AI Foundations for Managers"
TITLE = "ReadyHome"
TAGLINE = ("A friendly chat that gives mixed households a disaster-readiness score "
           "out of 10 and three small, mostly free next steps, each linked to "
           "official guidance.")


# --- measured numbers -------------------------------------------------------
def tokenomics() -> dict:
    """The two measured runs, keyed by label."""
    path = ROOT / "docs" / "tokenomics.json"
    runs = json.loads(path.read_text())
    return {r["label"]: r for r in runs}


SHIPPED = "trimmed history (shipped)"
BEFORE = "full history (before optimisation)"

TEST_COUNT = 236
TEST_FILES = 12


def pct_drop(before: float, after: float) -> float:
    return round((before - after) / before * 100, 1)


# --- the real tester session -------------------------------------------------
# Measured from docs/tester_session.json, which is frozen from the database
# straight after the session so later test runs cannot dilute it.
def tester() -> dict:
    return json.loads((ROOT / "docs" / "tester_session.json").read_text())


# Verbatim, in the order he said them. Kept whole, including the criticism:
# a report that only quotes the praise is not evidence.
TESTER_QUOTES = [
    "I do this for a living and it's fun to see you do this.",
    "Curious if it works for the people who actually have equipment evac needs, given that our household doesn't.",
    "It says it's not medical advice, but is this financial advice?",
    "Name isn't anywhere on the page \u2014 from a branding perspective, not ideal.",
    "It is a little slow. Maybe I'm just impatient.",
    "For evacuation \u2014 out of your neighbourhood, but to where? If you wanted to ask questions it's not clear that you can.",
    "Chain of questions is redundant. I already said I don't have a plan, but it's asking me about my plan.",
    "Wow, I'm realising we have none of this stuff\u2026 we should get it together!",
    "Should the scores mean something? You should add some sort of indicator.",
]


# --- evidence ---------------------------------------------------------------
def injection_evidence() -> str:
    return (ROOT / "docs" / "injection_evidence.txt").read_text().strip()


def img(name: str, alt: str, caption: str, width: str = "100%") -> str:
    """Embed a figure as base64 so the HTML is self-contained."""
    path = ASSETS / name
    data = base64.b64encode(path.read_bytes()).decode()
    return (
        f'<figure><img src="data:image/jpeg;base64,{data}" alt="{alt}" '
        f'style="width:{width}"><figcaption>{caption}</figcaption></figure>'
    )


# --- sources ----------------------------------------------------------------
SOURCES = {
    "fema2024": ("FEMA 2024 National Household Survey on Disaster Preparedness "
                 "(copy of FEMA's slides; the original was not located on fema.gov)",
                 "https://survivingcascadia.com/wp-content/uploads/2025/05/2024-national-household-survey-on-disaster-preparedness-findings.pdf"),
    "cdc_older": ("CDC, Preventing Chronic Disease (2008), "
                  "“Disaster Preparedness and the Chronic Disease Needs of Vulnerable Older Adults”",
                  "https://www.cdc.gov/PCD/ISSUES/2008/jan/07_0135.htm"),
    "ajem_pets": ("Australian Journal of Emergency Management (2015), "
                  "preparedness and evacuation behaviour of pet owners",
                  "https://knowledge.aidr.org.au/resources/ajem-apr-2015-the-preparedness-and-evacuation-behaviour-of-pet-owners-in-emergencies-and-natural-disasters/"),
    "ready_kit": ("Ready.gov, Build A Kit", "https://www.ready.gov/kit"),
    "ready_lowcost": ("Ready.gov, Low and No Cost Preparedness",
                      "https://www.ready.gov/collection/low-and-no-cost-preparedness"),
    "cdc_infant": ("CDC, Emergency infant and young child feeding checklist",
                   "https://www.cdc.gov/nutrition/emergencies-infant-feeding/checklist.html"),
    "aap": ("American Academy of Pediatrics, Disaster preparedness resources for families",
            "https://www.aap.org/en/patient-care/disasters-and-children/resources-for-families/"),
    "redcross_kit": ("American Red Cross store, 4-person 3-day emergency preparedness kit",
                     "https://www.redcross.org/store/4-person-3-day-emergency-preparedness-kit/91053.html"),
    "redcross_app": ("American Red Cross Emergency app",
                     "https://apps.apple.com/US/app/id954783878"),
    "fema_app": ("PCWorld overview of emergency preparedness apps, including the FEMA app",
                 "https://www.pcworld.com/article/3537459/5-apps-to-prepare-you-for-any-emergency.html"),
    "stear": ("Texas Division of Emergency Management, State of Texas Emergency Assistance Registry",
              "https://tdem.texas.gov/response/state-of-texas-emergency-assistance-registry"),
    "acl": ("Administration for Community Living, Emergency preparedness",
            "https://www.acl.gov/programs/emergency-preparedness"),
    "hhs": ("HHS emPOWER Program", "https://empowerprogram.hhs.gov/about.html"),
    "redcross_pets": ("American Red Cross, Make pets part of your emergency plans",
                      "https://www.redcross.org/about-us/news-and-events/news/2025/make-pets-part-of-your-emergency-plans.html"),
}


def cite(key: str) -> str:
    label, url = SOURCES[key]
    return f'<a href="{url}">{label}</a>'
