#!/usr/bin/env python3
"""Local/CI catalog refresh: scrape -> validate -> archive -> generate README.

Pass --fixture for a mocked-HTTP dry-run. Do not push listings to main; the
daily GitHub Action opens a pull request instead.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

from scripts.apply_seeds import restore_missing_fallbacks
from scripts.archive_closed import archive_catalog_files
from scripts.catalog_publication import publish_files, recover_publication
from scripts.generate_dashboard import write_readme
from scripts.refresh_diagnostics import diagnostics_path, write_diagnostics
from scripts.scrape_internships import scrape_and_merge
from scripts.validate_data import (
    CatalogValidationError,
    report_validation,
    validate_catalogs,
    validation_summary,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.json"
DEFAULT_SEASON = REPO_ROOT / "config" / "current_season.json"
DEFAULT_README = REPO_ROOT / "README.md"
DEFAULT_INACTIVE = REPO_ROOT / "README-Inactive.md"
DEFAULT_NEWEST = REPO_ROOT / "README-Newest.md"
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
    fixture_map_path: Path | None = None,
    today: str | None = None,
    readme_path: Path = DEFAULT_README,
    inactive_path: Path = DEFAULT_INACTIVE,
    newest_path: Path = DEFAULT_NEWEST,
    health_path: Path = DEFAULT_HEALTH,
    season_path: Path = DEFAULT_SEASON,
    artifact_path: Path = DEFAULT_ARTIFACT,
    schema_path: Path = DEFAULT_SCHEMA,
) -> int:
    """Compute a full candidate snapshot, then publish it as a recoverable set."""
    destinations = [
        Path(path)
        for path in (
            catalog_path,
            archived_path,
            health_path,
            readme_path,
            inactive_path,
            newest_path,
        )
    ]
    protected = {path.resolve() for path in destinations}
    if len(protected) != 6 or Path(artifact_path).resolve() in protected:
        raise ValueError("refresh outputs and scraper artifact must use distinct destinations")
    diagnostic_directory = diagnostics_path(Path(artifact_path)).resolve()
    if any(
        path == diagnostic_directory or diagnostic_directory in path.parents for path in protected
    ):
        raise ValueError("diagnostic files must be separate from published outputs")
    if (fixture_path is not None or fixture_map_path is not None) and destinations[
        0
    ].resolve() == DEFAULT_CATALOG.resolve():
        raise ValueError("refusing to merge fixtures into the production catalog")
    progress = {
        "phase": "recovery",
        "today": date.fromisoformat(today or date.today().isoformat()).isoformat(),
    }
    candidates = []
    reported = False

    def report_failure(error=None):
        nonlocal reported
        if reported:
            return
        if isinstance(error, CatalogValidationError):
            progress["phase"] = error.phase + "_validation"
            progress.update(validation_summary(error.errors))
        try:
            write_diagnostics(Path(artifact_path), progress, candidates)
            reported = True
        except OSError:
            print("[FAIL] Diagnostics could not be saved; retain publication recovery files.")

    try:
        recover_publication(destinations)
        with tempfile.TemporaryDirectory(prefix="catalog-refresh-") as temporary:
            stage = Path(temporary)
            candidates = [stage / str(index) for index in range(len(destinations))]
            progress["phase"] = "staging"
            for source, candidate in zip(destinations[:2], candidates[:2]):
                if source.exists():
                    shutil.copyfile(source, candidate)
                else:
                    candidate.write_text("[]", encoding="utf-8")
            try:
                result = _generate_catalog(
                    catalog_path=candidates[0],
                    archived_path=candidates[1],
                    health_path=candidates[2],
                    readme_path=candidates[3],
                    inactive_path=candidates[4],
                    newest_path=candidates[5],
                    fixture_path=fixture_path,
                    fixture_map_path=fixture_map_path,
                    today=today,
                    season_path=season_path,
                    artifact_path=artifact_path,
                    schema_path=schema_path,
                    progress=progress,
                )
                if result:
                    report_failure()
                    return result
                progress["phase"] = "publication"
                publish_files(candidates, destinations)
            except Exception as exc:
                report_failure(exc)
                raise
        return 0
    except Exception as exc:
        report_failure(exc)
        print(f"[FAIL] Refresh failed ({type(exc).__name__}); inspect publication recovery state.")
        return 1


def _generate_catalog(
    *,
    catalog_path: Path = DEFAULT_CATALOG,
    archived_path: Path = DEFAULT_ARCHIVED,
    fixture_path: Path | None = None,
    fixture_map_path: Path | None = None,
    today: str | None = None,
    readme_path: Path = DEFAULT_README,
    inactive_path: Path = DEFAULT_INACTIVE,
    newest_path: Path = DEFAULT_NEWEST,
    health_path: Path = DEFAULT_HEALTH,
    season_path: Path = DEFAULT_SEASON,
    artifact_path: Path = DEFAULT_ARTIFACT,
    schema_path: Path = DEFAULT_SCHEMA,
    progress: dict | None = None,
) -> int:
    """Run scrape -> validate -> archive -> generate README. Return 0 on success."""
    sweep_day = today or date.today().isoformat()
    progress = progress if progress is not None else {}

    def validate(phase):
        progress["phase"] = phase + "_validation"
        errors = validate_catalogs(
            catalog_path,
            archived_path,
            json.loads(Path(schema_path).read_text(encoding="utf-8")),
            phase=phase,
        )
        progress.update(validation_summary(errors))
        return report_validation(errors)

    if validate("input") != 0:
        return 1
    use_fixtures = fixture_path is not None or fixture_map_path is not None
    progress["phase"] = "scrape"
    scrape_and_merge(
        catalog_path=catalog_path,
        fixture_path=fixture_path,
        fixture_map_path=fixture_map_path,
        seen_on=sweep_day,
        rate_limit_delay=0 if use_fixtures else 1.0,
        artifact_path=artifact_path,
        season_path=season_path,
    )
    failed_scrapers = load_failed_scrapers(artifact_path)
    # Export only company names from the maintainer-owned allowlist.
    allowlist = json.loads((REPO_ROOT / "config/allowlist.json").read_text(encoding="utf-8"))
    approved = {entry["name"] for entry in allowlist["companies"]}
    progress["failed_scrapers"] = [name for name in failed_scrapers if name in approved]
    if validate("input") != 0:
        return 1
    probe_session = None
    if not use_fixtures:
        import requests

        probe_session = requests.Session()
    progress["phase"] = "archive"
    archive_catalog_files(
        catalog_path,
        archived_path,
        today=sweep_day,
        session=probe_session,
        unavailable_companies=set(failed_scrapers),
        schema_path=schema_path,
    )
    progress["phase"] = "fallback_restoration"
    restore_missing_fallbacks(
        catalog_path,
        DEFAULT_SEEDS,
        season_path=season_path,
        seen_on=sweep_day,
        archived_path=archived_path,
    )
    active = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    archived = json.loads(Path(archived_path).read_text(encoding="utf-8"))
    if validate("final") != 0:
        return 1
    progress["validated"] = True
    progress["phase"] = "health"
    write_health(
        health_path,
        today=sweep_day,
        active=active,
        archived=archived,
        failed_scrapers=failed_scrapers,
    )
    progress["phase"] = "generation"
    write_readme(
        internships_path=catalog_path,
        archived_path=archived_path,
        season_path=season_path,
        readme_path=readme_path,
        inactive_path=inactive_path,
        newest_path=newest_path,
        health_path=health_path,
        now=date.fromisoformat(sweep_day),
    )
    return validate("final")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--archived", type=Path, default=DEFAULT_ARCHIVED)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Local single-company JSON fixture (Boston Scientific). Omit for a live sweep.",
    )
    parser.add_argument(
        "--fixture-map",
        type=Path,
        default=None,
        help="JSON map of company -> fixture path for multi-company dry-runs",
    )
    parser.add_argument("--today", default=None)
    parser.add_argument("--season-file", type=Path, default=DEFAULT_SEASON)
    parser.add_argument("--readme", type=Path, default=DEFAULT_README)
    parser.add_argument("--inactive", type=Path, default=DEFAULT_INACTIVE)
    parser.add_argument("--newest", type=Path, default=DEFAULT_NEWEST)
    parser.add_argument("--health", type=Path, default=DEFAULT_HEALTH)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args(argv)
    return refresh_catalog(
        catalog_path=args.catalog,
        archived_path=args.archived,
        fixture_path=args.fixture,
        fixture_map_path=args.fixture_map,
        today=args.today,
        season_path=args.season_file,
        readme_path=args.readme,
        inactive_path=args.inactive,
        newest_path=args.newest,
        health_path=args.health,
        artifact_path=args.artifact,
    )


if __name__ == "__main__":
    sys.exit(main())
