"""Mocked ingestion checks: all JSON adapters preserve shared eligibility evidence."""

import json
from unittest.mock import Mock

import pytest
from scripts.scraper_framework import InternshipScraper, discover_scrapers

from test_qualification_contract import CASES

CONTRACT_COMPANIES = [
    "Boston Scientific",
    "Inspire Medical",
    "Penumbra",
    "Abbott",
    "Intuitive",
    "Align",
    "Hologic",
    "Edwards",
    "Stryker",
    "Medtronic",
]


@pytest.mark.parametrize("company", CONTRACT_COMPANIES)
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_contract_through_adapters(company, case):
    for text in (
        case["text"],
        "<p>" + case["text"].replace("\n", "</p><p>") + "</p>",
    ):
        payload = board_payload(
            company, {"description": text}, title=case.get("title", "Software Intern")
        )
        session = response_session(payload)
        if isinstance(payload, str):
            session.get.return_value.text = payload
        result = discover_scrapers()[company](session=session, rate_limit_delay=0).scrape(
            "2026-10-28", season="summer-2027"
        )
        assert not result.blocked, result.error
        assert bool(result.postings) == (case["outcome"] == "accept")
        assert bool(result.reviews) == (case["outcome"] == "review")
        if result.reviews:
            assert result.reviews[0]["qualifications"]
            assert any(
                "description" in item["source"] for item in result.reviews[0]["qualifications"]
            )


def response_session(payload):
    response = Mock(status_code=200, text=json.dumps(payload))
    response.json.return_value = payload
    session = Mock()
    session.get.return_value = response
    session.post.return_value = response
    return session


def board_payload(company, evidence, *, title="Software Intern"):
    location = "Boston, MA, United States"
    url = "https://example.com/jobs/123"
    job = dict(evidence)
    if company == "Boston Scientific":
        job.update(name=title, id=123, locations=[location], positionUrl=url)
        return {"data": {"count": 1, "positions": [job]}}
    if company == "Inspire Medical":
        job.update(title=title, id=123, absolute_url=url, location={"name": location})
        return {"jobs": [job]}
    if company == "Penumbra":
        job.update(text=title, id=123, hostedUrl=url, categories={"location": location})
        return [job]
    if company == "Abbott":
        job.update(title=title, reqId=123, applyUrl=url, cityStateCountry=location)
        return {"refineSearch": {"data": {"jobs": [job]}}}
    if company == "Intuitive":
        job.update(name=title, id=123, postingUrl=url, location={"fullLocation": location})
        return {"content": [job], "totalFound": 1}
    if company == "Align":
        job.update(title=title, id=123, url=url, location={"name": location})
        return {"data": [job]}
    if company == "Hologic":
        job.update(Title=title, Id=123, PrimaryLocation=location, PrimaryLocationCountry="US")
        return {"items": [{"requisitionList": [job], "TotalJobsCount": 1}]}
    if company == "Edwards":
        job.update(JobPostingTitle=title, id=123, ApplyUrl=url, Location=location)
        return {"results": [{"hits": [job], "nbPages": 1}]}
    if company == "Stryker":
        job.update(
            title=title,
            requisitionID=123,
            applyURL=url,
            locations=[{"locationParsedText": location, "countryAbbr": "US"}],
        )
        return "window.__PRELOAD_STATE__ = " + json.dumps({"jobSearch": {"jobs": [job]}})
    assert company == "Medtronic"
    job.update(
        {
            "@type": "JobPosting",
            "title": title,
            "url": url,
            "jobLocation": {
                "address": {
                    "addressLocality": "Boston",
                    "addressRegion": "MA",
                    "addressCountry": "US",
                }
            },
        }
    )
    return '<script type="application/ld+json">' + json.dumps(job) + "</script>"


@pytest.mark.parametrize(
    "company",
    [
        "Boston Scientific",
        "Inspire Medical",
        "Penumbra",
        "Abbott",
        "Intuitive",
        "Align",
        "Hologic",
        "Edwards",
        "Stryker",
        "Medtronic",
    ],
)
@pytest.mark.parametrize(
    "evidence,expected",
    [
        ({"description": "Develop software; no sponsorship available."}, True),
        ({"description": "Must be pursuing a PhD in computer science."}, False),
        (
            {
                "description": "Currently enrolled in a PhD program with Python experience preferred."
            },
            False,
        ),
        ({"description": "This internship is in Fall."}, False),
        ({"description": "This internship is for Fall."}, False),
        ({"degree": "PhD only"}, False),
        ({"educationRequirements": "BS/MS/PhD"}, True),
        (
            {
                "degreeRequirements": "Doctorate required.",
                "education": "Bachelor degree completed.",
            },
            False,
        ),
        (
            {
                "degreeRequirements": "Bachelor degree completed.",
                "education": "Doctorate required.",
            },
            False,
        ),
        ({"degreeRequirements": "PhD", "education": "Bachelor degree completed."}, False),
        ({"educationRequirements": ["BS", "MS", "PhD"]}, True),
        ({"degreeRequirements": "PhD preferred", "education": "Bachelor degree required."}, True),
        ({"season": "summer-2026"}, False),
        ({"description": "Summer 2026 internship."}, False),
    ],
)
def test_adapters_pass_available_evidence_to_shared_gate(company, evidence, expected):
    payload = board_payload(company, evidence)
    session = response_session(payload)
    if isinstance(payload, str):
        session.get.return_value.text = payload
    scraper = discover_scrapers()[company](session=session, rate_limit_delay=0)
    result = scraper.scrape(seen_on="2026-10-19", season="summer-2027")
    assert not result.blocked, result.error
    assert bool(result.postings) is expected
    if expected:
        assert result.postings[0]["season"] == "summer-2027"
        assert "description" not in result.postings[0]
        assert "degree_requirements" not in result.postings[0]


def test_base_class_enforces_eligibility_even_without_listing_cache():
    class DirectScraper(InternshipScraper):
        company = "Boston Scientific"

        def find_posting_urls(self):
            return ["https://example.com/jobs/123"]

        def parse_posting(self, url):
            return {
                "title": "Summer 2026 Software Intern",
                "location": "Boston, MA",
                "apply_url": url,
            }

    assert DirectScraper().scrape("2026-10-19", season="summer-2027").postings == []


def test_explicit_target_does_not_get_prefiltered_using_default_season():
    payload = board_payload("Boston Scientific", {"season": "summer-2028"})
    scraper = discover_scrapers()["Boston Scientific"](
        session=response_session(payload),
        rate_limit_delay=0,
    )
    assert len(scraper.scrape("2026-10-19", season="summer-2028").postings) == 1


def test_runner_uses_requested_season_file(tmp_path):
    from scripts.scrape_internships import scrape_and_merge

    catalog = tmp_path / "active.json"
    catalog.write_text("[]", encoding="utf-8")
    season_file = tmp_path / "season.json"
    season_file.write_text('{"season": "summer-2028"}', encoding="utf-8")
    fixture = tmp_path / "jobs.json"
    payload = board_payload("Boston Scientific", {"season": "summer-2028"})
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    rows = scrape_and_merge(catalog, fixture_path=fixture, season_path=season_file)
    assert len(rows) == 1
    assert rows[0]["season"] == "summer-2028"


def test_reviewed_cleanup_removes_invalid_row_and_preserves_identity(tmp_path):
    from scripts.archive_closed import archive_catalog_files
    from scripts.scraper_framework import upsert_catalog
    from scripts.validate_data import run_validation

    scraper = discover_scrapers()["Boston Scientific"](rate_limit_delay=0)
    invalid = scraper.to_catalog_row(
        {
            "title": "Finance GBS Intern",
            "location": "Boston, MA",
            "apply_url": "https://example.com/jobs/finance",
            "req_id": "FIN-123",
        },
        seen_on="2026-10-01",
        season="summer-2027",
    )
    valid = scraper.to_catalog_row(
        {
            "title": "Software Intern",
            "location": "Boston, MA",
            "apply_url": "https://example.com/jobs/software",
            "req_id": "SWE-123",
        },
        seen_on="2026-10-19",
        season="summer-2027",
    )
    # Discovery alone cannot remove an existing ID.
    merged = upsert_catalog([invalid, valid], [valid], seen_on="2026-10-19")
    assert invalid in merged
    active_path = tmp_path / "active.json"
    archived_path = tmp_path / "archived.json"
    active_path.write_text(json.dumps(merged), encoding="utf-8")
    archived_path.write_text("[]", encoding="utf-8")
    assert run_validation(active_path, archived_path) == 0
    active, archived = archive_catalog_files(
        active_path,
        archived_path,
        today="2026-10-19",
        force_close_ids=[invalid["id"]],
    )
    assert active == [valid]
    assert len(archived) == 1
    for key, value in invalid.items():
        assert archived[0][key] == value
    assert archived[0]["close_reason"] == "force_close"
    assert archived[0]["closed_at"] == "2026-10-19"
    assert run_validation(active_path, archived_path) == 0
