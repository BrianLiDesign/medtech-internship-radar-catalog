"""Hub-landing intern adapters — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers, upsert_catalog

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hub_landing_jobs.html"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"

HUB_COMPANIES = {
    "Medtronic": "MedtronicScraper",
    "Insulet": "InsuletScraper",
    "Tandem": "TandemScraper",
    "Smith+Nephew": "SmithNephewScraper",
    "ResMed": "ResMedScraper",
    "Globus Medical": "GlobusMedicalScraper",
    "Biotronik": "BiotronikScraper",
    "Alcon": "AlconScraper",
}


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


def test_hub_landing_companies_are_registered():
    scrapers = discover_scrapers()
    for company, class_name in HUB_COMPANIES.items():
        assert company in scrapers
        assert scrapers[company].__name__ == class_name
    assert "Hub Landing Internship" not in scrapers


def test_medtronic_fixture_keeps_us_stem_intern_and_drops_others():
    session = _html_session(FIXTURE.read_text(encoding="utf-8"))
    result = discover_scrapers()["Medtronic"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    url = session.get.call_args[0][0]
    assert "early-careers.html" in url
    titles = [row["title"] for row in result.postings]
    assert titles == ["Software Engineer Intern", "R&D Intern"]
    row = result.postings[0]
    assert row["company"] == "Medtronic"
    assert row["row_kind"] == "posting"
    assert row["ats"] == "workday"
    assert row["req_id"] == "R1001"
    assert "Minneapolis" in row["location"]
    assert "United States" in row["location"]
    assert row["apply_url"].endswith("Software-Engineer-Intern_R1001")
    assert row["role_family"] == "Software"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    for posting in result.postings:
        assert list(Draft7Validator(schema).iter_errors(posting)) == []
    rd = result.postings[1]
    assert rd["location"] == "Austin, TX, United States"
    assert rd["role_family"] == "BME/R&D"
    assert "valhalla" not in rd["apply_url"]
    assert "people/" not in rd["apply_url"]


def test_empty_hub_keeps_program_fallback():
    hub = {
        "id": "insulet-hub",
        "company": "Insulet",
        "title": "Student opportunities",
        "apply_url": "https://www.insulet.com/working-at-insulet/students-and-early-careers",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    result = discover_scrapers()["Insulet"](
        session=_html_session("<html><title>Student Opportunities</title></html>"),
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is False
    assert upsert_catalog([hub], result.postings, seen_on="2026-08-15") == [hub]


def test_hub_landing_soft_fail_on_forbidden(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    result = discover_scrapers()["Alcon"](
        session=_html_session("no", status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Alcon"


def test_medtronic_browser_wall_soft_fails(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    html = "<html><body>Incorrect Browser</body></html>"
    result = discover_scrapers()["Medtronic"](
        session=_html_session(html),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-15")
    assert result.postings == []
    assert result.blocked is True
    assert json.loads(artifact.read_text(encoding="utf-8"))["company"] == "Medtronic"
