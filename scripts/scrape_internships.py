#!/usr/bin/env python3
"""Run allowlisted internship scrapers and upsert posting rows.

Workday companies without an adapter stay on program_fallback. Candidate
Pass --fixture to merge a mocked PCSX JSON payload into a **temp** catalog
(never `data/active/internships.json`). Pass --fixture-map for multi-company
dry-runs. Live refresh omits both.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from catalog.io import load_json_list, write_json_list

from scraper_framework import discover_scrapers, upsert_catalog
from validate_data import run_validation

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.json"
DEFAULT_ALLOWLIST = REPO_ROOT / "config" / "allowlist.json"
DEFAULT_CANDIDATES = REPO_ROOT / "config" / "candidates.json"
DEFAULT_ARTIFACT = REPO_ROOT / "logs" / "scrape_failures.json"
DEFAULT_FIXTURE_MAP = REPO_ROOT / "config" / "fixtures" / "scrape_map.json"


class FixtureResponse:
    """Minimal JSON response object for fixture sessions."""

    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.text = json.dumps(payload)

    def json(self) -> dict:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FixtureHtmlResponse:
    """Minimal HTML response object for fixture sessions."""

    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code
        self.headers = {"Content-Type": "text/html; charset=utf-8"}

    def json(self) -> dict:
        raise ValueError("not json")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FixtureSession:
    """Session that returns a local JSON or HTML fixture for every request."""

    def __init__(self, payload: dict | str) -> None:
        self.payload = payload

    def get(self, url: str, timeout: float | None = None, headers: dict | None = None):
        del url, timeout, headers
        if isinstance(self.payload, dict):
            return FixtureResponse(self.payload)
        return FixtureHtmlResponse(self.payload)


def load_fixture_map(path: Path) -> dict[str, Path]:
    """Load company → fixture path entries relative to the repo root."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: fixture map must be a JSON object")
    resolved: dict[str, Path] = {}
    for company, relative in payload.items():
        resolved[str(company)] = (REPO_ROOT / str(relative)).resolve()
    return resolved


def fixture_session_for(path: Path) -> FixtureSession:
    text = Path(path).read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return FixtureSession(json.loads(text))
    return FixtureSession(text)


def load_company_names(path: Path, key: str) -> set[str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {item["name"] for item in payload.get(key, [])}


def scrape_and_merge(
    catalog_path: Path,
    *,
    fixture_path: Path | None = None,
    fixture_map_path: Path | None = None,
    seen_on: str | None = None,
    rate_limit_delay: float = 1.0,
    artifact_path: Path | None = None,
    allowlist_path: Path = DEFAULT_ALLOWLIST,
    candidates_path: Path = DEFAULT_CANDIDATES,
) -> list[dict]:
    """Discover allowlisted scrapers, scrape, upsert by internship ID, and save."""
    if (fixture_path is not None or fixture_map_path is not None) and Path(
        catalog_path
    ).resolve() == DEFAULT_CATALOG.resolve():
        raise ValueError(
            "refusing to merge fixtures into the production catalog "
            "(data/active/internships.json); pass --catalog to a temp file"
        )
    seen = seen_on or date.today().isoformat()
    existing = load_json_list(catalog_path)
    allowlist = load_company_names(allowlist_path, "companies")
    candidates = load_company_names(candidates_path, "candidates")
    fixture_companies: dict[str, Path] | None = None
    if fixture_map_path is not None:
        fixture_companies = load_fixture_map(fixture_map_path)
    elif fixture_path is not None:
        fixture_companies = {"Boston Scientific": Path(fixture_path)}
    use_fixtures = fixture_companies is not None
    delay = 0 if use_fixtures else rate_limit_delay
    merged = existing
    failures: list[dict] = []
    _write_failure_artifact(artifact_path, failures)
    for company, scraper_cls in discover_scrapers().items():
        if company not in allowlist or company in candidates:
            continue
        if use_fixtures and company not in fixture_companies:
            continue
        session = None
        if use_fixtures:
            session = fixture_session_for(fixture_companies[company])
        try:
            scraper = scraper_cls(
                session=session,
                rate_limit_delay=delay,
                artifact_path=None,
            )
            result = scraper.scrape(seen_on=seen)
            if result.blocked:
                failures.append(
                    {
                        "company": company,
                        "blocked": True,
                        "error": result.error,
                    }
                )
                continue
            merged = upsert_catalog(merged, result.postings, seen_on=seen)
        except Exception as exc:
            failures.append(
                {
                    "company": company,
                    "blocked": True,
                    "error": str(exc),
                }
            )
            continue
    _write_failure_artifact(artifact_path, failures)
    write_json_list(catalog_path, merged)
    return merged


def _write_failure_artifact(artifact_path: Path | None, failures: list[dict]) -> None:
    if artifact_path is None:
        return
    output = Path(artifact_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Local single-company JSON fixture (Boston Scientific only)",
    )
    parser.add_argument(
        "--fixture-map",
        type=Path,
        default=None,
        help="JSON map of company name → fixture path for multi-company dry-runs",
    )
    parser.add_argument("--seen-on", default=None)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args(argv)
    scrape_and_merge(
        catalog_path=args.catalog,
        fixture_path=args.fixture,
        fixture_map_path=args.fixture_map,
        seen_on=args.seen_on,
        artifact_path=args.artifact,
    )
    return run_validation(args.catalog, DEFAULT_ARCHIVED, DEFAULT_SCHEMA)


if __name__ == "__main__":
    sys.exit(main())
