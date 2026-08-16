"""Phenom widget adapters — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "phenom_widgets.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"

PHENOM_COMPANIES = {
    "Abbott": "AbbottScraper",
    "Zimmer Biomet": "ZimmerBiometScraper",
    "GE HealthCare": "GEHealthCareScraper",
    "STERIS": "SterisScraper",
    "CONMED": "ConmedScraper",
    "Philips": "PhilipsScraper",
    "Siemens Healthineers": "SiemensHealthineersScraper",
}


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


def test_phenom_companies_are_registered():
    scrapers = discover_scrapers()
    for company, class_name in PHENOM_COMPANIES.items():
        assert company in scrapers
        assert scrapers[company].__name__ == class_name
    assert "Phenom Internship" not in scrapers


def test_abbott_phenom_fixture_keeps_us_stem_intern_and_drops_others():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    session = _json_session(payload)
    result = discover_scrapers()["Abbott"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.post.assert_called()
    posted_url, posted_kwargs = session.post.call_args[0][0], session.post.call_args[1]
    posted_body = posted_kwargs["json"]
    assert posted_url == "https://www.jobs.abbott/widgets"
    assert posted_body["ddoKey"] == "refineSearch"
    assert posted_body["keywords"] == "intern"
    assert [row["title"] for row in result.postings] == ["Software Engineer Intern"]
    row = result.postings[0]
    assert row["company"] == "Abbott"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "phenom"
    assert row["req_id"] == "US-SWE-1"
    assert row["posted_at"] == "2026-04-15"
    assert row["role_family"] == "Software"
    assert "United States" in row["location"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_phenom_unexpected_payload_is_blocked(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["CONMED"](
        session=_json_session({"message": "ok"}),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "CONMED"


def test_empty_phenom_board_keeps_program_fallback():
    payload = {"refineSearch": {"data": {"jobs": []}}}
    hub = {
        "id": "abbott-hub",
        "company": "Abbott",
        "title": "University Internship Program",
        "apply_url": "https://www.jobs.abbott/us/en/university-internship-program",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["Abbott"](
        session=_json_session(payload),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_phenom_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Philips"](
        session=_json_session({"message": "no"}, status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Philips"
