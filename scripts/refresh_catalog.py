#!/usr/bin/env python3
"""Local/CI catalog refresh: scrape → validate → archive → generate README.

Pass --fixture for a mocked-HTTP dry-run. Do not push listings to main; the
daily GitHub Action opens a pull request instead.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from apply_seeds import restore_missing_fallbacks
from archive_closed import archive_catalog_files
from generate_dashboard import write_readme
from scrape_internships import scrape_and_merge
from validate_data import run_validation

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.json"
DEFAULT_SEASON = REPO_ROOT / "config" / "current_season.json"
DEFAULT_README = REPO_ROOT / "README.md"
DEFAULT_INACTIVE = REPO_ROOT / "README-Inactive.md"
DEFAULT_HEALTH = REPO_ROOT / "data" / "health.json"
DEFAULT_ARTIFACT = REPO_ROOT / "logs" / "scrape_failures.json"
DEFAULT_SEEDS = REPO_ROOT / "config" / "seeds" / "program_fallbacks.json"


def load_failed_scrapers(artifact_path: Path) -> list[str]:
    path = Path(artifact_path)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and payload.get("blocked") and payload.get("company"):
        return [str(payload["company"])]
    if isinstance(payload, list):
        return [
            str(item["company"])
            for item in payload
            if isinstance(item, dict) and item.get("blocked") and item.get("company")
        ]
    return []


def write_health(
    health_path: Path,
    *,
    today: str,
    active: list[dict],
    archived: list[dict],
    failed_scrapers: list[str],
) -> dict:
    """Write sweep health metadata for the README stats strip."""
    health = {
        "last_sweep": today,
        "updated_count": sum(1 for row in active if row.get("last_seen") == today),
        "failed_scrapers": failed_scrapers,
        "archived_count": len(archived),
    }
    output = Path(health_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(health, indent=2) + "\n", encoding="utf-8")
    return health


def refresh_catalog(
    *,
    catalog_path: Path = DEFAULT_CATALOG,
    archived_path: Path = DEFAULT_ARCHIVED,
    fixture_path: Path | None = None,
    today: str | None = None,
    readme_path: Path = DEFAULT_README,
    inactive_path: Path = DEFAULT_INACTIVE,
    health_path: Path = DEFAULT_HEALTH,
    season_path: Path = DEFAULT_SEASON,
    artifact_path: Path = DEFAULT_ARTIFACT,
    schema_path: Path = DEFAULT_SCHEMA,
) -> int:
    """Run scrape → validate → archive → generate README. Return 0 on success."""
    sweep_day = today or date.today().isoformat()
    scrape_and_merge(
        catalog_path=catalog_path,
        fixture_path=fixture_path,
        seen_on=sweep_day,
        rate_limit_delay=0 if fixture_path is not None else 1.0,
        artifact_path=artifact_path,
    )
    if run_validation(catalog_path, archived_path, schema_path) != 0:
        return 1
    probe_session = None
    if fixture_path is None:
        import requests

        probe_session = requests.Session()
    archive_catalog_files(
        catalog_path,
        archived_path,
        today=sweep_day,
        session=probe_session,
    )
    restore_missing_fallbacks(
        catalog_path,
        DEFAULT_SEEDS,
        season_path=season_path,
        seen_on=sweep_day,
    )
    active = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    archived = json.loads(Path(archived_path).read_text(encoding="utf-8"))
    write_health(
        health_path,
        today=sweep_day,
        active=active,
        archived=archived,
        failed_scrapers=load_failed_scrapers(artifact_path),
    )
    write_readme(
        internships_path=catalog_path,
        archived_path=archived_path,
        season_path=season_path,
        readme_path=readme_path,
        inactive_path=inactive_path,
        health_path=health_path,
        now=date.fromisoformat(sweep_day),
    )
    return run_validation(catalog_path, archived_path, schema_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--archived", type=Path, default=DEFAULT_ARCHIVED)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Local ATS JSON fixture (no live HTTP). Omit for a live sweep.",
    )
    parser.add_argument("--today", default=None)
    parser.add_argument("--readme", type=Path, default=DEFAULT_README)
    parser.add_argument("--inactive", type=Path, default=DEFAULT_INACTIVE)
    parser.add_argument("--health", type=Path, default=DEFAULT_HEALTH)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args(argv)
    return refresh_catalog(
        catalog_path=args.catalog,
        archived_path=args.archived,
        fixture_path=args.fixture,
        today=args.today,
        readme_path=args.readme,
        inactive_path=args.inactive,
        health_path=args.health,
        artifact_path=args.artifact,
    )


if __name__ == "__main__":
    sys.exit(main())
