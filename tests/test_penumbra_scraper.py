"""Penumbra Lever adapter — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "penumbra_lever.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"


def _json_session(payload, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = {"Content-Type": "application/json"}
    response.text = json.dumps(payload)
    response.json.return_value = payload
    session = Mock()
    session.get.return_value = response
    return session


def test_framework_registers_penumbra_scraper():
    scrapers = discover_scrapers()
    assert "Penumbra" in scrapers
    assert scrapers["Penumbra"].__name__ == "PenumbraScraper"


def test_penumbra_fixture_keeps_us_stem_intern_and_drops_hr_and_non_us():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = discover_scrapers()["Penumbra"](
        session=_json_session(payload),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    by_title = {row["title"]: row for row in result.postings}
    assert set(by_title) == {
        "Software Engineer Intern",
        "Quality Engineer Intern",
        "Manufacturing Engineer Intern",
    }
    swe = by_title["Software Engineer Intern"]
    assert swe["company"] == "Penumbra"
    assert swe["row_kind"] == "posting"
    assert swe["source"] == "scrape"
    assert swe["ats"] == "lever"
    assert swe["location"] == "Alameda, CA"
    assert swe["req_id"] == "us-swe-intern"
    assert swe["posted_at"] == "2025-06-15"
    assert swe["apply_url"] == "https://jobs.lever.co/penumbrainc/us-swe-intern"
    assert swe["role_family"] == "Software"
    assert by_title["Quality Engineer Intern"]["location"] == "Remote (US)"
    assert by_title["Quality Engineer Intern"]["role_family"] == "Quality/manufacturing"
    assert by_title["Manufacturing Engineer Intern"]["location"] == "Alameda, United States"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for row in result.postings:
        assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_penumbra_empty_board_yields_no_postings():
    result = discover_scrapers()["Penumbra"](
        session=_json_session([]),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False


def test_penumbra_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Penumbra"](
        session=_json_session({"message": "Not authorized"}, status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["company"] == "Penumbra"
    assert payload["blocked"] is True


def test_penumbra_empty_board_keeps_existing_program_fallback():
    from scraper_framework import upsert_catalog

    hub = {
        "id": "penumbra-hub",
        "company": "Penumbra",
        "title": "Internships",
        "apply_url": "https://jobs.lever.co/penumbrainc",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["Penumbra"](
        session=_json_session([]),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    merged = upsert_catalog([hub], result.postings, seen_on="2026-08-15")
    assert merged == [hub]


def test_penumbra_unexpected_object_payload_is_blocked(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Penumbra"](
        session=_json_session({"jobs": []}),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
