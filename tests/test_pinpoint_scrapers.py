"""Pinpoint adapters — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pinpoint_jobs.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"


def _json_session(payload, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = {"Content-Type": "application/json"}
    response.text = json.dumps(payload)
    response.json.return_value = payload
    session = Mock()
    session.get.return_value = response
    session.post.return_value = response
    return session


def test_align_is_registered():
    scrapers = discover_scrapers()
    assert scrapers["Align"].__name__ == "AlignScraper"
    assert "Pinpoint Internship" not in scrapers


def test_align_fixture_keeps_us_stem_intern_and_drops_others():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    session = _json_session(payload)
    result = discover_scrapers()["Align"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    assert session.get.call_args[0][0] == "https://jobs.aligntech.com/jobs.json"
    assert [row["title"] for row in result.postings] == ["Software Engineer Intern"]
    row = result.postings[0]
    assert row["company"] == "Align"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "pinpoint"
    assert row["req_id"] == "ALGN-INT-1"
    assert row["posted_at"] == "2026-04-15"
    assert row["location"] == "San Jose, California, United States"
    assert row["apply_url"] == "https://jobs-aligntech.aligntech.com/en/jobs/1001"
    assert row["role_family"] == "Software"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_empty_pinpoint_board_keeps_program_fallback():
    hub = {
        "id": "align-hub",
        "company": "Align",
        "title": "Summer Internship Program",
        "apply_url": "https://jobs.aligntech.com/careers",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["Align"](
        session=_json_session({"data": []}),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_pinpoint_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Align"](
        session=_json_session({"message": "no"}, status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Align"
