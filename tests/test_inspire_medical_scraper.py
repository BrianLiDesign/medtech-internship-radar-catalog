"""Inspire Medical Greenhouse adapter — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "inspire_greenhouse.json"
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


def test_framework_registers_inspire_medical_scraper():
    scrapers = discover_scrapers()
    assert "Inspire Medical" in scrapers
    assert scrapers["Inspire Medical"].__name__ == "InspireMedicalScraper"


def test_inspire_fixture_keeps_rd_intern_and_drops_ft_and_marketing():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = discover_scrapers()["Inspire Medical"](
        session=_json_session(payload),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert [row["title"] for row in result.postings] == ["R&D Engineering Intern"]
    row = result.postings[0]
    assert row["company"] == "Inspire Medical"
    assert row["row_kind"] == "posting"
    assert row["source"] == "scrape"
    assert row["ats"] == "greenhouse"
    assert row["location"] == "Minneapolis, MN"
    assert row["req_id"] == "INS-INT-1"
    assert row["posted_at"] == "2026-04-15"
    assert row["apply_url"] == (
        "https://job-boards.greenhouse.io/inspiremedicalsystemsinc/jobs/111001"
    )
    assert row["role_family"] == "BME/R&D"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_inspire_intern_less_board_yields_no_postings():
    payload = {
        "jobs": [
            {
                "id": 1,
                "title": "Territory Manager - Austin",
                "location": {"name": "Austin, TX"},
                "absolute_url": "https://job-boards.greenhouse.io/inspiremedicalsystemsinc/jobs/1",
            }
        ],
        "meta": {"total": 1},
    }
    result = discover_scrapers()["Inspire Medical"](
        session=_json_session(payload),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False


def test_inspire_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Inspire Medical"](
        session=_json_session({"message": "Not authorized"}, status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["company"] == "Inspire Medical"
    assert payload["blocked"] is True


def test_inspire_updated_at_used_when_first_published_missing():
    payload = {
        "jobs": [
            {
                "id": 444004,
                "title": "Biomedical Engineer Intern",
                "updated_at": "2026-03-20T12:00:00-05:00",
                "location": {"name": "Minneapolis, MN"},
                "absolute_url": "https://job-boards.greenhouse.io/inspiremedicalsystemsinc/jobs/444004",
            }
        ],
        "meta": {"total": 1},
    }
    result = discover_scrapers()["Inspire Medical"](
        session=_json_session(payload),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert len(result.postings) == 1
    assert result.postings[0]["posted_at"] == "2026-03-20"


def test_inspire_intern_less_board_keeps_existing_program_fallback():
    from scraper_framework import upsert_catalog

    hub = {
        "id": "inspire-hub",
        "company": "Inspire Medical",
        "title": "Internship Program",
        "apply_url": "https://www.inspiresleep.com/en-us/careers/internships/",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    payload = {
        "jobs": [
            {
                "id": 1,
                "title": "Territory Manager - Austin",
                "location": {"name": "Austin, TX"},
                "absolute_url": "https://job-boards.greenhouse.io/inspiremedicalsystemsinc/jobs/1",
            }
        ],
        "meta": {"total": 1},
    }
    result = discover_scrapers()["Inspire Medical"](
        session=_json_session(payload),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    merged = upsert_catalog([hub], result.postings, seen_on="2026-08-15")
    assert merged == [hub]
