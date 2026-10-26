"""Every link shown to a user is a real, vetted source (REQUIREMENTS.md 7)."""

from app import kb
from app.verifier import check_text

ALLOWED = kb.ALLOWED_DOMAINS + ("tdem.texas.gov",)


def _host(url: str) -> str:
    return url.split("/")[2].removeprefix("www.")


def test_every_source_is_on_an_allowed_domain():
    for source_id, source in kb.sources().items():
        host = _host(source["source_url"])
        assert any(host == d or host.endswith("." + d) for d in ALLOWED), (source_id, host)


def test_every_source_has_a_publisher_and_a_title():
    for source_id, source in kb.sources().items():
        assert source["publisher"].strip(), source_id
        assert source["title"].strip(), source_id
        assert source["source_url"].startswith("https://"), source_id


def test_no_duplicate_urls():
    urls = [s["source_url"] for s in kb.sources().values()]
    assert len(urls) == len(set(urls))


def test_every_step_offers_further_reading():
    for step in kb.steps():
        assert step["source_ids"], f"{step['id']} has nothing to read"


def test_the_bigger_steps_offer_more_than_one_article():
    """The steps people struggle with should point somewhere to learn more."""
    for step_id in ("kit-phases", "family-plan", "pet-kit-lodging", "backup-power"):
        step = kb.step_by_id(step_id)
        assert len(step["source_ids"]) >= 2, step_id


def test_source_titles_are_distinct_within_a_step():
    """Two chips reading the same thing is a dead end for the user."""
    for step in kb.steps():
        titles = [kb.source(s)["title"] for s in step["source_ids"] if kb.source(s)]
        assert len(titles) == len(set(titles)), step["id"]


def test_the_verifier_accepts_every_url_the_kb_ships():
    for url in kb.allowed_urls():
        assert check_text(f"See {url}").flagged == []
