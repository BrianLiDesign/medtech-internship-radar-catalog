"""Oracle Recruiting CE adapters — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "oracle_ce_requisitions.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"

ORACLE_COMPANIES = {
    "CooperCompanies": "CooperCompaniesScraper",
    "Hologic": "HologicScraper",
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


def test_oracle_ce_companies_are_registered():
    scrapers = discover_scrapers()
    for company, class_name in ORACLE_COMPANIES.items():
        assert company in scrapers
        assert scrapers[company].__name__ == class_name
    assert "Oracle CE Internship" not in scrapers


def test_cooper_fixture_keeps_us_stem_intern_and_drops_others():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    session = _json_session(payload)
    result = discover_scrapers()["CooperCompanies"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    url = session.get.call_args[0][0]
    assert (
        "hcjy.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions" in url
    )
    assert "finder=" in url
    assert [row["title"] for row in result.postings] == ["Software Engineer Intern"]
    row = result.postings[0]
    assert row["company"] == "CooperCompanies"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "oracle"
    assert row["req_id"] == "US-SWE-1"
    assert row["posted_at"] == "2026-04-15"
    assert "Victor" in row["location"]
    assert "New York" in row["location"]
    assert row["apply_url"] == (
        "https://hcjy.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/US-SWE-1"
    )
    assert row["role_family"] == "Software"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_hologic_uses_cx_site():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    session = _json_session(payload)
    discover_scrapers()["Hologic"](session=session, rate_limit_delay=0).scrape(seen_on="2026-08-15")
    url = session.get.call_args[0][0]
    assert "ebwb.fa.us2.oraclecloud.com" in url
    assert "siteNumber=CX," in url or "siteNumber=CX&" in url or "siteNumber%3DCX" in url


def test_empty_oracle_board_keeps_program_fallback():
    payload = {"items": [{"TotalJobsCount": 0, "requisitionList": []}], "count": 1}
    hub = {
        "id": "cooper-hub",
        "company": "CooperCompanies",
        "title": "Global Internship Program",
        "apply_url": "https://www.coopercos.com/global-internship-program/",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["CooperCompanies"](
        session=_json_session(payload),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_oracle_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Hologic"](
        session=_json_session({"message": "no"}, status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Hologic"


def test_oracle_unexpected_payload_is_blocked(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["CooperCompanies"](
        session=_json_session({"message": "ok"}),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
