"""Local catalog refresh dry-run: scrape → validate → archive → generate README."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BSC_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boston_scientific_pcsx.json"
FIXTURE_MAP = REPO_ROOT / "config" / "fixtures" / "scrape_map.json"


def test_posting_can_be_archived_rediscovered_and_archived_again(tmp_path, monkeypatch):
    import requests
    from scripts.archive_closed import archive_catalog_files
    from scripts.refresh_catalog import refresh_catalog

    def no_network(*args, **kwargs):
        raise AssertionError("lifecycle test must not use live HTTP")

    monkeypatch.setattr(requests.Session, "get", no_network)
    catalog = tmp_path / "active.json"
    archived = tmp_path / "archived.json"
    catalog.write_text("[]", encoding="utf-8")
    archived.write_text("[]", encoding="utf-8")
    empty_map = tmp_path / "empty-map.json"
    empty_map.write_text("{}", encoding="utf-8")

    def refresh(day, discover):
        assert (
            refresh_catalog(
                catalog_path=catalog,
                archived_path=archived,
                fixture_path=BSC_FIXTURE if discover else None,
                fixture_map_path=None if discover else empty_map,
                today=day,
                readme_path=tmp_path / "README.md",
                inactive_path=tmp_path / "README-Inactive.md",
                newest_path=tmp_path / "README-Newest.md",
                health_path=tmp_path / "health.json",
                artifact_path=tmp_path / "failures.json",
            )
            == 0
        )
        active_rows = json.loads(catalog.read_text(encoding="utf-8"))
        archived_rows = json.loads(archived.read_text(encoding="utf-8"))
        active_ids = {row["id"] for row in active_rows}
        archived_ids = {row["id"] for row in archived_rows}
        assert active_ids.isdisjoint(archived_ids)
        assert len(archived_ids) == len(archived_rows)
        return active_rows, archived_rows

    active, _ = refresh("2026-08-14", True)
    original = next(row for row in active if row["row_kind"] == "posting")
    archive_catalog_files(catalog, archived, today="2026-08-15", force_close_ids=[original["id"]])
    active, closed = refresh("2026-08-16", True)
    reopened = next(row for row in active if row["id"] == original["id"])
    assert reopened["first_seen"] == original["first_seen"]
    assert reopened["last_seen"] == "2026-08-16"
    assert "closed_at" not in reopened
    assert "close_reason" not in reopened
    assert not any(row["id"] == original["id"] for row in closed)
    refresh("2026-08-17", False)
    for day in ["2026-08-18", "2026-08-18", "2026-08-19"]:
        active, closed = refresh(day, False)
        assert not any(row["id"] == original["id"] for row in active)
        matches = [row for row in closed if row["id"] == original["id"]]
        assert len(matches) == 1
        assert matches[0]["first_seen"] == original["first_seen"]
        assert matches[0]["closed_at"] == "2026-08-18"
        assert matches[0]["close_reason"] == "consecutive_misses"


@pytest.mark.parametrize("outcome", ["recovered", "url_dead", "force_close"])
def test_fixture_pipeline_preserves_daily_streak_and_fallback_closure(
    tmp_path, monkeypatch, outcome
):
    import requests
    import scripts.refresh_catalog as refresh
    from scripts.apply_seeds import load_seed_document, row_from_seed
    from scripts.archive_closed import archive_catalog_files

    def no_network(*args, **kwargs):
        raise AssertionError("fixture pipeline must not use live HTTP")

    monkeypatch.setattr(requests.Session, "get", no_network)
    seed = next(
        seed
        for seed in load_seed_document(refresh.DEFAULT_SEEDS)["seeds"]
        if seed["company"] == "Medtronic"
    )
    row = row_from_seed(seed, season="summer-2027", seen_on="2026-08-13")
    catalog = tmp_path / "active.json"
    archived = tmp_path / "archived.json"
    catalog.write_text(json.dumps([row]), encoding="utf-8")
    archived.write_text("[]", encoding="utf-8")
    session = Mock()
    response = Mock(status_code=200, text="")

    def fixture_probe(url, **kwargs):
        return response if url == row["program_url"] else Mock(status_code=200, text="")

    session.get.side_effect = fixture_probe
    force_ids = []

    def archive_with_fixture_probe(*args, **kwargs):
        kwargs["session"] = session
        kwargs["force_close_ids"] = force_ids
        return archive_catalog_files(*args, **kwargs)

    monkeypatch.setattr(refresh, "archive_catalog_files", archive_with_fixture_probe)
    checks = [("2026-08-14", 404, 1), ("2026-08-14", 404, 1)]
    if outcome == "recovered":
        checks += [("2026-08-15", 200, 0), ("2026-08-16", 404, 1)]
    else:
        checks += [("2026-08-15", 410, None), ("2026-08-16", 200, None)]
    for day, status, expected in checks:
        response.status_code = status
        force_ids = [row["id"]] if outcome == "force_close" and day == "2026-08-15" else []
        assert (
            refresh.refresh_catalog(
                catalog_path=catalog,
                archived_path=archived,
                fixture_path=BSC_FIXTURE,
                today=day,
                readme_path=tmp_path / "README.md",
                inactive_path=tmp_path / "README-Inactive.md",
                newest_path=tmp_path / "README-Newest.md",
                health_path=tmp_path / "health.json",
                artifact_path=tmp_path / "failures.json",
            )
            == 0
        )
        active_rows = json.loads(catalog.read_text(encoding="utf-8"))
        closed_rows = json.loads(archived.read_text(encoding="utf-8"))
        matching = [item for item in active_rows if item["id"] == row["id"]]
        if expected is not None:
            assert matching[0]["miss_count"] == expected
            assert not any(item["id"] == row["id"] for item in closed_rows)
        else:
            assert matching == []
            closed = [item for item in closed_rows if item["id"] == row["id"]]
            assert len(closed) == 1
            assert closed[0]["close_reason"] == outcome
            assert closed[0]["closed_at"] == "2026-08-15"
            assert "Medtronic" not in (tmp_path / "README.md").read_text(encoding="utf-8")
            assert "Medtronic" in (tmp_path / "README-Inactive.md").read_text(encoding="utf-8")


def test_local_dry_run_scrape_validate_archive_generate_without_network(tmp_path, monkeypatch):
    import requests
    from scripts.refresh_catalog import refresh_catalog

    def _no_live_http(*args, **kwargs):
        raise AssertionError("live network is not allowed in the dry-run")

    monkeypatch.setattr(requests.Session, "get", _no_live_http)
    monkeypatch.setattr(requests, "get", _no_live_http)

    catalog_path = tmp_path / "active.json"
    archived_path = tmp_path / "archived.json"
    catalog_path.write_text(
        (REPO_ROOT / "data" / "active" / "internships.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    archived_path.write_text("[]\n", encoding="utf-8")
    readme_path = tmp_path / "README.md"
    inactive_path = tmp_path / "README-Inactive.md"
    newest_path = tmp_path / "README-Newest.md"
    health_path = tmp_path / "health.json"

    result = refresh_catalog(
        catalog_path=catalog_path,
        archived_path=archived_path,
        fixture_path=BSC_FIXTURE,
        today="2026-08-14",
        readme_path=readme_path,
        inactive_path=inactive_path,
        newest_path=newest_path,
        health_path=health_path,
        season_path=REPO_ROOT / "config" / "current_season.json",
        artifact_path=tmp_path / "scrape_failures.json",
    )

    assert result == 0
    readme = readme_path.read_text(encoding="utf-8")
    assert "Boston Scientific" in readme
    assert "Student Program Radar" not in readme
    assert readme_path.exists()
    assert inactive_path.exists()
    assert newest_path.exists()
    newest = newest_path.read_text(encoding="utf-8")
    assert newest.startswith("# Newest internships")
    assert "[README-Newest.md](README-Newest.md)" in readme
    health = json.loads(health_path.read_text(encoding="utf-8"))
    assert health["last_sweep"] == "2026-08-14"
    assert "archived_count" in health
    assert "updated_count" in health
    rows = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert any(
        row["company"] == "Boston Scientific" and row["row_kind"] == "posting" for row in rows
    )
    assert "Inspire Medical" in {row["company"] for row in rows}


def test_fixture_map_dry_run_scrapes_mapped_adapter_families(tmp_path, monkeypatch):
    import requests
    from scripts.refresh_catalog import refresh_catalog

    def _no_live_http(*args, **kwargs):
        raise AssertionError("live network is not allowed in the dry-run")

    monkeypatch.setattr(requests.Session, "get", _no_live_http)
    monkeypatch.setattr(requests, "get", _no_live_http)

    catalog_path = tmp_path / "active.json"
    archived_path = tmp_path / "archived.json"
    catalog_path.write_text("[]\n", encoding="utf-8")
    archived_path.write_text("[]\n", encoding="utf-8")

    result = refresh_catalog(
        catalog_path=catalog_path,
        archived_path=archived_path,
        fixture_map_path=FIXTURE_MAP,
        today="2026-08-14",
        readme_path=tmp_path / "README.md",
        inactive_path=tmp_path / "README-Inactive.md",
        newest_path=tmp_path / "README-Newest.md",
        health_path=tmp_path / "health.json",
        season_path=REPO_ROOT / "config" / "current_season.json",
        artifact_path=tmp_path / "scrape_failures.json",
    )

    assert result == 0
    rows = json.loads(catalog_path.read_text(encoding="utf-8"))
    companies = {row["company"] for row in rows if row.get("row_kind") == "posting"}
    assert "Boston Scientific" in companies
    assert "Inspire Medical" in companies
    assert "Medtronic" in companies
    assert len(companies) >= 8
