"""Edwards Algolia InstantSearch adapter — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "edwards_algolia.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"

ALGOLIA_URL = "https://ltjqzme6d2-dsn.algolia.net/1/indexes/*/queries"


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


def test_edwards_is_registered():
    scrapers = discover_scrapers()
    assert scrapers["Edwards"].__name__ == "EdwardsScraper"
    assert "Algolia Internship" not in scrapers


def test_edwards_fixture_keeps_us_stem_intern_and_drops_others():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    session = _json_session(payload)
    result = discover_scrapers()["Edwards"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.post.assert_called()
    posted_url, posted_kwargs = session.post.call_args[0][0], session.post.call_args[1]
    assert posted_url == ALGOLIA_URL
    requests = posted_kwargs["json"]["requests"]
    assert requests[0]["indexName"] == "EdwardsCareersJobs"
    assert requests[0]["query"] == "intern"
    headers = posted_kwargs["headers"]
    assert headers["x-algolia-application-id"] == "LTJQZME6D2"
    assert "x-algolia-api-key" in headers
    assert [row["title"] for row in result.postings] == ["Software Engineer Intern"]
    row = result.postings[0]
    assert row["company"] == "Edwards"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "algolia"
    assert row["req_id"] == "Req-US-SWE-1"
    assert "United States" in row["location"]
    assert row["apply_url"].endswith("Software-Engineer-Intern_Req-US-SWE-1/apply")
    assert row["role_family"] == "Software"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []


def test_empty_edwards_board_keeps_program_fallback():
    payload = {"results": [{"hits": [], "nbHits": 0, "nbPages": 0, "page": 0}]}
    hub = {
        "id": "edwards-hub",
        "company": "Edwards",
        "title": "US Summer Internship Program",
        "apply_url": "https://www.edwards.com/careers/university-recruiting/internship-programs",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["Edwards"](
        session=_json_session(payload),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_edwards_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Edwards"](
        session=_json_session({"message": "no"}, status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Edwards"
