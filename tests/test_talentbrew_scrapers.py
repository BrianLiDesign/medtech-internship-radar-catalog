"""TalentBrew search-jobs adapters — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "talentbrew_search_jobs.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"

TALENTBREW_COMPANIES = {
    "BD": "BDScraper",
    "Baxter": "BaxterScraper",
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


def test_talentbrew_companies_are_registered():
    scrapers = discover_scrapers()
    for company, class_name in TALENTBREW_COMPANIES.items():
        assert company in scrapers
        assert scrapers[company].__name__ == class_name
    assert "TalentBrew Internship" not in scrapers


def test_bd_fixture_keeps_us_stem_intern_and_drops_others():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    session = _json_session(payload)
    result = discover_scrapers()["BD"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    url = session.get.call_args[0][0]
    assert "jobs.bd.com/en/search-jobs/results" in url
    assert "Keywords=intern" in url
    assert [row["title"] for row in result.postings] == ["Engineering Intern"]
    row = result.postings[0]
    assert row["company"] == "BD"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "talentbrew"
    assert row["req_id"] == "97591406352"
    assert row["posted_at"] == "2026-04-15"
    assert row["location"] == "Canaan, CT"
    assert (
        row["apply_url"] == "https://jobs.bd.com/en/job/canaan/engineering-intern/159/97591406352"
    )
    assert row["role_family"] == "Other STEM"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_empty_talentbrew_board_keeps_program_fallback():
    hub = {
        "id": "bd-hub",
        "company": "BD",
        "title": "Early Talent",
        "apply_url": "https://jobs.bd.com/en/early-talent",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["BD"](
        session=_json_session({"filters": "", "results": "", "hasJobs": False}),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_talentbrew_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Baxter"](
        session=_json_session({"message": "no"}, status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Baxter"


def test_talentbrew_unexpected_payload_is_blocked(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Baxter"](
        session=_json_session({"message": "ok"}),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
