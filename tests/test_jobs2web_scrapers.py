"""jobs2web career-site search adapters — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "jobs2web_search.html"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"

JOBS2WEB_COMPANIES = {
    "Teleflex": "TeleflexScraper",
    "Olympus": "OlympusScraper",
    "Arthrex": "ArthrexScraper",
}


def _html_session(html: str, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = {"Content-Type": "text/html;charset=UTF-8"}
    response.text = html
    response.json.side_effect = ValueError("not json")
    session = Mock()
    session.get.return_value = response
    session.post.return_value = response
    return session


def test_jobs2web_companies_are_registered():
    scrapers = discover_scrapers()
    for company, class_name in JOBS2WEB_COMPANIES.items():
        assert company in scrapers
        assert scrapers[company].__name__ == class_name
    assert "Jobs2web Internship" not in scrapers


def test_teleflex_fixture_keeps_us_stem_intern_and_drops_others():
    html = FIXTURE.read_text(encoding="utf-8")
    session = _html_session(html)
    result = discover_scrapers()["Teleflex"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    url = session.get.call_args[0][0]
    assert "careers.teleflex.com/search/" in url
    assert "q=intern" in url
    assert [row["title"] for row in result.postings] == [
        "Engineering Intern",
        "Software Intern",
    ]
    row = result.postings[0]
    assert row["company"] == "Teleflex"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "jobs2web"
    assert row["req_id"] == "1400000001"
    assert row["location"] == "Wayne, PA, US"
    assert (
        row["apply_url"]
        == "https://careers.teleflex.com/job/Wayne-Engineering-Intern-PA/1400000001/"
    )
    assert row["role_family"] == "Other STEM"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for posting in result.postings:
        assert list(Draft7Validator(schema).iter_errors(posting)) == []
    software = result.postings[1]
    assert software["location"] == "Naples, FL, US, 34108"
    assert software["req_id"] == "1368000006"
    assert software["role_family"] == "Software"


def test_empty_jobs2web_board_keeps_program_fallback():
    hub = {
        "id": "teleflex-hub",
        "company": "Teleflex",
        "title": "Careers",
        "apply_url": "https://careers.teleflex.com/",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["Teleflex"](
        session=_html_session("<html><title>Intern - Teleflex Jobs</title></html>"),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_jobs2web_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Teleflex"](
        session=_html_session("no", status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Teleflex"
