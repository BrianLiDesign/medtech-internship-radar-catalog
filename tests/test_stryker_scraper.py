"""Stryker Paradox career-site adapters — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "stryker_jobs.html"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"


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


def test_stryker_is_registered():
    scrapers = discover_scrapers()
    assert scrapers["Stryker"].__name__ == "StrykerScraper"


def test_stryker_fixture_keeps_us_stem_intern_and_drops_others():
    session = _html_session(FIXTURE.read_text(encoding="utf-8"))
    result = discover_scrapers()["Stryker"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    url = session.get.call_args[0][0]
    assert "careers.stryker.com/jobs" in url
    assert "keyword=intern" in url
    assert [row["title"] for row in result.postings] == ["Engineering Intern"]
    row = result.postings[0]
    assert row["company"] == "Stryker"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "paradox"
    assert row["req_id"] == "R100001"
    assert row["location"] == "Portage, MI 49002, United States"
    assert (
        row["apply_url"]
        == "https://stryker.wd1.myworkdayjobs.com/StrykerCareers/job/Portage-Michigan/Engineering-Intern_R100001"
    )
    assert row["role_family"] == "Other STEM"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_empty_stryker_board_keeps_program_fallback():
    hub = {
        "id": "stryker-hub",
        "company": "Stryker",
        "title": "Students and Graduates",
        "apply_url": "https://careers.stryker.com/students-and-graduates",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    html = '<script>window.__PRELOAD_STATE__ = {"jobSearch":{"totalJob":0,"jobs":[]}};</script>'
    result = discover_scrapers()["Stryker"](
        session=_html_session(html),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_stryker_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Stryker"](
        session=_html_session("no", status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Stryker"
