"""J&J internships-page adapters — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "jnj_internships.html"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"
HUB = "https://www.careers.jnj.com/en/early-career-programs/internships/"


def _html_session(html: str, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = {"Content-Type": "text/html; charset=utf-8"}
    response.text = html
    response.json.side_effect = ValueError("not json")
    session = Mock()
    session.get.return_value = response
    session.post.return_value = response
    return session


def test_jnj_medtech_is_registered():
    scrapers = discover_scrapers()
    assert scrapers["J&J MedTech"].__name__ == "JJMedTechScraper"


def test_jnj_fixture_keeps_us_stem_intern_and_drops_others():
    session = _html_session(FIXTURE.read_text(encoding="utf-8"))
    result = discover_scrapers()["J&J MedTech"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    assert session.get.call_args[0][0] == HUB
    assert [row["title"] for row in result.postings] == ["Engineering Intern"]
    row = result.postings[0]
    assert row["company"] == "J&J MedTech"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "jnj"
    assert row["req_id"] == "r-100001"
    assert row["location"] == "Irvine, CA"
    assert row["apply_url"] == "https://www.careers.jnj.com/en/jobs/r-100001/engineering-intern/"
    assert row["role_family"] == "Other STEM"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_empty_jnj_listing_keeps_program_fallback():
    hub = {
        "id": "jnj-hub",
        "company": "J&J MedTech",
        "title": "Internships",
        "apply_url": HUB,
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["J&J MedTech"](
        session=_html_session("<html><title>Internships at J&amp;J</title></html>"),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_jnj_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["J&J MedTech"](
        session=_html_session("no", status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "J&J MedTech"
