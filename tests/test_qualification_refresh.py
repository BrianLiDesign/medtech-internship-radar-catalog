"""Run the same independent contract through real adapters and staged publication."""

import json
from unittest.mock import Mock

import pytest
from scripts.refresh_catalog import refresh_catalog
from scripts.scraper_framework import InternshipScraper, ScrapeResult

from test_ingestion_eligibility import CONTRACT_COMPANIES, board_payload
from test_qualification_contract import CASES


def refresh(tmp_path, fixtures, day):
    active, archived = tmp_path / "active.json", tmp_path / "archived.json"
    if not active.exists():
        active.write_text("[]", encoding="utf-8")
        archived.write_text("[]", encoding="utf-8")
    fixture_map = {}
    for company, payload in fixtures.items():
        path = tmp_path / (
            company.replace(" ", "_") + (".html" if isinstance(payload, str) else ".json")
        )
        path.write_text(
            payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8"
        )
        fixture_map[company] = str(path)
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps(fixture_map), encoding="utf-8")
    assert (
        refresh_catalog(
            catalog_path=active,
            archived_path=archived,
            fixture_map_path=mapping,
            today=day,
            readme_path=tmp_path / "README.md",
            inactive_path=tmp_path / "inactive.md",
            newest_path=tmp_path / "newest.md",
            health_path=tmp_path / "health.json",
            artifact_path=tmp_path / "failures.json",
        )
        == 0
    )
    return json.loads(active.read_text(encoding="utf-8")), json.loads(
        archived.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_contract_refreshes_all_adapters_without_live_http(tmp_path, monkeypatch, case):
    import requests

    def no_network(*args, **kwargs):
        raise AssertionError("contract refresh must use mocked HTTP")

    monkeypatch.setattr(requests.Session, "get", no_network)
    monkeypatch.setattr(requests.Session, "post", no_network)
    payloads = {
        company: board_payload(
            company, {"description": case["text"]}, title=case.get("title", "Software Intern")
        )
        for company in CONTRACT_COMPANIES
    }
    active, _ = refresh(tmp_path, payloads, "2026-10-28")
    postings = [row for row in active if row["row_kind"] == "posting"]
    assert {row["company"] for row in postings} == (
        set(CONTRACT_COMPANIES) if case["outcome"] == "accept" else set()
    )
    original = {row["company"]: row for row in postings}
    active, _ = refresh(tmp_path, payloads, "2026-10-29")
    for row in active:
        if row["row_kind"] == "posting":
            assert row["id"] == original[row["company"]]["id"]
            assert row["first_seen"] == "2026-10-28"
            assert row["last_seen"] == "2026-10-29"
            assert "description" not in row
    reviews = json.loads(
        (tmp_path / "failures-qualification-reviews.json").read_text(encoding="utf-8")
    )
    assert {item["company"] for item in reviews} == (
        set(CONTRACT_COMPANIES) if case["outcome"] == "review" else set()
    )
    assert json.loads((tmp_path / "failures.json").read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("withheld", ["PhD required.", "PhD may be required depending on project."])
def test_withheld_and_blocked_rows_have_distinct_archive_evidence(tmp_path, monkeypatch, withheld):
    import requests
    import scripts.scrape_internships as runner
    from scripts.scraper_framework import discover_scrapers

    monkeypatch.setattr(requests.Session, "get", Mock(side_effect=AssertionError("no live HTTP")))
    good = {
        company: board_payload(company, {"description": "BS/MS/PhD"})
        for company in CONTRACT_COMPANIES
    }
    active, _ = refresh(tmp_path, good, "2026-10-28")
    original = {row["company"]: row for row in active if row["row_kind"] == "posting"}

    class Blocked(InternshipScraper):
        company = "Abbott"

        def find_posting_urls(self):
            return []

        def parse_posting(self, url):
            return None

        def scrape(self, seen_on, season=None):
            return ScrapeResult(company=self.company, blocked=True, error="HTTP 503")

    classes = discover_scrapers()
    classes["Abbott"] = Blocked
    monkeypatch.setattr(runner, "discover_scrapers", lambda: classes)
    payloads = dict(good)
    payloads["Boston Scientific"] = board_payload("Boston Scientific", {"description": withheld})
    for day in ("2026-10-29", "2026-10-29", "2026-10-30"):
        active, archived = refresh(tmp_path, payloads, day)
        by_id = {row["id"]: row for row in active}
        blocked = by_id[original["Abbott"]["id"]]
        assert blocked["last_seen"] == "2026-10-28"
        assert blocked["miss_count"] == 0
        assert by_id[original["Penumbra"]["id"]]["last_seen"] == day
        if day == "2026-10-29":
            assert by_id[original["Boston Scientific"]["id"]]["miss_count"] == 1
        else:
            assert original["Boston Scientific"]["id"] not in by_id
            matches = [row for row in archived if row["id"] == original["Boston Scientific"]["id"]]
            assert len(matches) == 1
            assert matches[0]["close_reason"] == "consecutive_misses"
            assert matches[0]["first_seen"] == original["Boston Scientific"]["first_seen"]
        review_rows = json.loads(
            (tmp_path / "failures-qualification-reviews.json").read_text(encoding="utf-8")
        )
        if "depending" in withheld:
            assert review_rows[0]["id"] == original["Boston Scientific"]["id"]
            assert review_rows[0]["seen_on"] == day
        else:
            assert review_rows == []
    # Clarified/accepted evidence reopens the same ID, preserving first_seen.
    active, archived = refresh(tmp_path, good, "2026-10-31")
    reopened = next(row for row in active if row["id"] == original["Boston Scientific"]["id"])
    assert reopened["first_seen"] == "2026-10-28"
    assert reopened["miss_count"] == 0
    assert not any(row["id"] == reopened["id"] for row in archived)
    assert (
        json.loads((tmp_path / "failures-qualification-reviews.json").read_text(encoding="utf-8"))
        == []
    )


def test_review_evidence_cannot_overwrite_a_published_output(tmp_path):
    active = tmp_path / "failures-qualification-reviews.json"
    active.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="distinct destinations"):
        refresh_catalog(
            catalog_path=active,
            archived_path=tmp_path / "archived.json",
            health_path=tmp_path / "health.json",
            readme_path=tmp_path / "README.md",
            inactive_path=tmp_path / "inactive.md",
            newest_path=tmp_path / "newest.md",
            artifact_path=tmp_path / "failures.json",
        )
    assert active.read_text(encoding="utf-8") == "[]"
