"""Integra LifeSciences Kentico job-search adapter — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "integra_jobs_search.html"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"

SEARCH_PATH = "www.integralife.com/api/jobs/search"


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


def test_integra_is_registered():
    scrapers = discover_scrapers()
    assert scrapers["Integra LifeSciences"].__name__ == "IntegraLifeSciencesScraper"
    assert "Kentico Jobs Internship" not in scrapers


def test_integra_fixture_keeps_us_stem_intern_and_drops_others():
    session = _html_session(FIXTURE.read_text(encoding="utf-8"))
    result = discover_scrapers()["Integra LifeSciences"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    url = session.get.call_args[0][0]
    assert SEARCH_PATH in url
    assert "keyword=intern" in url
    assert "pageUrl=%2Fcareers%2Fjob-search" in url or "pageUrl=/careers/job-search" in url
    assert [row["title"] for row in result.postings] == ["Software Engineer Intern"]
    row = result.postings[0]
    assert row["company"] == "Integra LifeSciences"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "kentico"
    assert row["req_id"] == "JR-1001"
    assert "New Jersey" in row["location"]
    assert row["apply_url"].endswith("Software-Engineer-Intern_JR-1001")
    assert row["role_family"] == "Software"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_empty_integra_board_keeps_program_fallback():
    html = """
<div data-partial-heading>Search for: &quot;intern&quot;</div>
<div data-partial-count>0 results found</div>
<div data-partial-results></div>
"""
    hub = {
        "id": "integra-hub",
        "company": "Integra LifeSciences",
        "title": "Early Talent & Student Opportunities",
        "apply_url": "https://www.integralife.com/careers/career-areas/early-talent-student-opportunities",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["Integra LifeSciences"](
        session=_html_session(html),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_integra_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Integra LifeSciences"](
        session=_html_session("no", status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Integra LifeSciences"
