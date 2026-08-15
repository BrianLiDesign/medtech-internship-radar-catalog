"""Internship scraper framework — registration, ingest, and merge."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from jsonschema import Draft7Validator

from internship_ids import internship_id
from scraper_framework import discover_scrapers, upsert_catalog

PCSX_ONE_INTERN = {
    "status": 200,
    "data": {
        "count": 1,
        "positions": [
            {
                "id": 563602809367335,
                "displayJobId": "627000",
                "name": "R&D Systems Engineering Intern",
                "locations": ["Arden Hills, MN, United States"],
                "atsJobId": "627000",
                "positionUrl": "/careers/job/563602809367335",
                "postedTs": 1750000000,
                "department": "Interns/Graduates",
            }
        ],
    },
}


def _json_session(payload: dict, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = {"Content-Type": "application/json"}
    response.text = json.dumps(payload)
    response.json.return_value = payload
    if status_code >= 400:
        response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    else:
        response.raise_for_status.return_value = None
    session = Mock()
    session.get.return_value = response
    return session


def test_framework_registers_a_scraper_by_company_scraper_name():
    scrapers = discover_scrapers()
    assert "Boston Scientific" in scrapers
    assert scrapers["Boston Scientific"].__name__ == "BostonScientificScraper"


def test_mocked_http_postings_upsert_by_id_freezing_first_seen():
    req_id = "627000"
    row_id = internship_id({"company": "Boston Scientific", "req_id": req_id})
    existing = [
        {
            "id": row_id,
            "company": "Boston Scientific",
            "title": "R&D Systems Engineering Intern",
            "apply_url": "https://bostonscientific.eightfold.ai/careers/job/563602809367335",
            "season": "summer-2027",
            "role_family": "BME/R&D",
            "location": "Arden Hills, MN, United States",
            "degree": "unspecified",
            "row_kind": "posting",
            "source": "scrape",
            "first_seen": "2026-01-15",
            "last_seen": "2026-01-15",
            "req_id": req_id,
        }
    ]
    scraper_cls = discover_scrapers()["Boston Scientific"]
    scraper = scraper_cls(
        session=_json_session(PCSX_ONE_INTERN),
        rate_limit_delay=0,
    )
    result = scraper.scrape(seen_on="2026-08-14")
    merged = upsert_catalog(existing, result.postings, seen_on="2026-08-14")
    row = next(item for item in merged if item["id"] == row_id)
    assert row["first_seen"] == "2026-01-15"
    assert row["last_seen"] == "2026-08-14"
    assert row["source"] == "scrape"
    assert row["row_kind"] == "posting"


def test_inclusion_drops_hr_non_us_and_new_grad_from_scraped_postings():
    payload = {
        "status": 200,
        "data": {
            "count": 4,
            "positions": [
                {
                    "id": 1,
                    "atsJobId": "STEM-1",
                    "name": "Software Engineer Intern",
                    "locations": ["Marlborough, MA, United States"],
                    "positionUrl": "/careers/job/1",
                },
                {
                    "id": 2,
                    "atsJobId": "HR-1",
                    "name": "HR Intern",
                    "locations": ["Marlborough, MA, United States"],
                    "positionUrl": "/careers/job/2",
                },
                {
                    "id": 3,
                    "atsJobId": "EU-1",
                    "name": "Software Engineer Intern",
                    "locations": ["London, UK"],
                    "positionUrl": "/careers/job/3",
                },
                {
                    "id": 4,
                    "atsJobId": "NG-1",
                    "name": "New Grad Software Engineer",
                    "locations": ["Arden Hills, MN, United States"],
                    "positionUrl": "/careers/job/4",
                },
            ],
        },
    }
    scraper_cls = discover_scrapers()["Boston Scientific"]
    result = scraper_cls(session=_json_session(payload), rate_limit_delay=0).scrape(
        seen_on="2026-08-14"
    )
    titles = [row["title"] for row in result.postings]
    assert titles == ["Software Engineer Intern"]
    assert all(row["location"] == "Marlborough, MA, United States" for row in result.postings)


def test_soft_fail_when_blocked_produces_no_fake_rows(tmp_path):
    artifact = tmp_path / "scrape_failures.json"
    scraper_cls = discover_scrapers()["Boston Scientific"]
    result = scraper_cls(
        session=_json_session({"message": "Not authorized for PCSX"}, status_code=403),
        rate_limit_delay=0,
        artifact_path=artifact,
    ).scrape(seen_on="2026-08-14")
    assert result.postings == []
    assert result.blocked is True
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["company"] == "Boston Scientific"
    assert payload["blocked"] is True
    assert payload["error"]


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
BSC_FIXTURE = FIXTURE_DIR / "boston_scientific_pcsx.json"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"


def test_boston_scientific_fixture_scrape_yields_posting_rows():
    payload = json.loads(BSC_FIXTURE.read_text(encoding="utf-8"))
    scraper_cls = discover_scrapers()["Boston Scientific"]
    result = scraper_cls(session=_json_session(payload), rate_limit_delay=0).scrape(
        seen_on="2026-08-14"
    )
    assert result.postings, "expected at least one posting from the Eightfold fixture"
    assert {row["row_kind"] for row in result.postings} == {"posting"}
    assert {row["company"] for row in result.postings} == {"Boston Scientific"}
    assert {row["source"] for row in result.postings} == {"scrape"}
    titles = {row["title"] for row in result.postings}
    assert "R&D Systems Engineering Intern" in titles
    assert "Software Engineer Intern" in titles
    assert "HR Intern" not in titles
    assert "Finance GBS Intern" not in titles
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    for row in result.postings:
        errors = list(validator.iter_errors(row))
        assert errors == [], errors


def test_returning_and_citizen_only_tags_do_not_drop_the_row():
    payload = {
        "status": 200,
        "data": {
            "count": 1,
            "positions": [
                {
                    "id": 99,
                    "atsJobId": "RET-1",
                    "name": "Returning Software Engineer Intern — US citizens only",
                    "locations": ["Maple Grove, MN, United States"],
                    "positionUrl": "/careers/job/99",
                    "department": "Interns/Graduates; no sponsorship",
                }
            ],
        },
    }
    scraper_cls = discover_scrapers()["Boston Scientific"]
    result = scraper_cls(session=_json_session(payload), rate_limit_delay=0).scrape(
        seen_on="2026-08-14"
    )
    assert len(result.postings) == 1
    row = result.postings[0]
    assert row["eligibility"] == "returning"
    assert row["work_auth"] in {"citizen_only", "us_auth_no_sponsor"}
    assert row["row_kind"] == "posting"


def test_scrape_cli_merges_fixture_postings_and_keeps_other_fallbacks(tmp_path):
    from scrape_internships import scrape_and_merge

    repo_root = Path(__file__).resolve().parents[1]
    catalog_src = repo_root / "data" / "active" / "internships.json"
    catalog_path = tmp_path / "internships.json"
    catalog_path.write_text(catalog_src.read_text(encoding="utf-8"), encoding="utf-8")
    rows = scrape_and_merge(
        catalog_path=catalog_path,
        fixture_path=BSC_FIXTURE,
        seen_on="2026-08-14",
        rate_limit_delay=0,
    )
    written = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert written == rows
    bsc = [row for row in rows if row["company"] == "Boston Scientific"]
    others = [row for row in rows if row["company"] != "Boston Scientific"]
    assert bsc
    assert all(row["row_kind"] == "posting" for row in bsc)
    assert all(row["source"] == "scrape" for row in bsc)
    assert all(row["row_kind"] == "program_fallback" for row in others)
    allowlist = {
        company["name"]
        for company in json.loads(
            (Path(__file__).resolve().parents[1] / "config" / "allowlist.json").read_text(
                encoding="utf-8"
            )
        )["companies"]
    }
    assert {row["company"] for row in others} == allowlist - {"Boston Scientific"}
    assert "Inspire Medical" in {row["company"] for row in rows}


def test_registered_scrapers_are_allowlisted_and_not_candidates():
    allowlist = {
        company["name"]
        for company in json.loads(
            (Path(__file__).resolve().parents[1] / "config" / "allowlist.json").read_text(
                encoding="utf-8"
            )
        )["companies"]
    }
    candidates = {
        candidate["name"]
        for candidate in json.loads(
            (Path(__file__).resolve().parents[1] / "config" / "candidates.json").read_text(
                encoding="utf-8"
            )
        )["candidates"]
    }
    registered = set(discover_scrapers())
    assert registered <= allowlist
    assert registered.isdisjoint(candidates)
