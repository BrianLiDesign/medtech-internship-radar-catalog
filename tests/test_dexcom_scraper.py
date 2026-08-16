"""Dexcom Eightfold PCSX adapter — mocked HTTP only."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from scraper_framework import discover_scrapers

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boston_scientific_pcsx.json"
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


def test_dexcom_is_registered():
    scrapers = discover_scrapers()
    assert scrapers["Dexcom"].__name__ == "DexcomScraper"
    assert "Eightfold Internship" not in scrapers


def test_dexcom_fixture_keeps_us_stem_interns_and_drops_hr():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    session = _json_session(payload)
    result = discover_scrapers()["Dexcom"](
        session=session,
        rate_limit_delay=0,
    ).scrape(seen_on="2026-08-15")
    session.get.assert_called()
    url = session.get.call_args[0][0]
    assert "careers.dexcom.com/api/pcsx/search" in url
    assert "domain=dexcom.com" in url
    titles = {row["title"] for row in result.postings}
    assert "Software Engineer Intern" in titles
    assert "R&D Systems Engineering Intern" in titles
    assert "HR Intern" not in titles
    row = next(item for item in result.postings if item["title"] == "Software Engineer Intern")
    assert row["company"] == "Dexcom"
    assert row["ats"] == "eightfold"
    assert row["apply_url"].startswith("https://careers.dexcom.com/")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(row)) == []
