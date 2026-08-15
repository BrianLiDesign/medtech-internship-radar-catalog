"""Local catalog refresh dry-run: scrape → validate → archive → generate README."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BSC_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boston_scientific_pcsx.json"


def test_local_dry_run_scrape_validate_archive_generate_without_network(tmp_path, monkeypatch):
    import requests

    from refresh_catalog import refresh_catalog

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
    health_path = tmp_path / "health.json"

    result = refresh_catalog(
        catalog_path=catalog_path,
        archived_path=archived_path,
        fixture_path=BSC_FIXTURE,
        today="2026-08-14",
        readme_path=readme_path,
        inactive_path=inactive_path,
        health_path=health_path,
        season_path=REPO_ROOT / "config" / "current_season.json",
    )

    assert result == 0
    readme = readme_path.read_text(encoding="utf-8")
    assert "Boston Scientific" in readme
    assert "Student Program Radar" not in readme
    assert readme_path.exists()
    assert inactive_path.exists()
    health = json.loads(health_path.read_text(encoding="utf-8"))
    assert health["last_sweep"] == "2026-08-14"
    assert "archived_count" in health
    assert "updated_count" in health
    rows = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert any(
        row["company"] == "Boston Scientific" and row["row_kind"] == "posting" for row in rows
    )
    assert "Inspire Medical" in {row["company"] for row in rows}
