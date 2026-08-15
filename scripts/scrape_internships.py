#!/usr/bin/env python3
"""Run allowlisted internship scrapers and upsert posting rows.

Workday companies without an adapter stay on program_fallback. Candidate
Pass --fixture to merge a mocked PCSX JSON payload into a **temp** catalog
(never `data/active/internships.json`). Live refresh omits --fixture.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from scraper_framework import discover_scrapers, upsert_catalog
from validate_data import run_validation

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.json"
DEFAULT_ALLOWLIST = REPO_ROOT / "config" / "allowlist.json"
DEFAULT_CANDIDATES = REPO_ROOT / "config" / "candidates.json"
DEFAULT_ARTIFACT = REPO_ROOT / "logs" / "scrape_failures.json"


class FixtureResponse:
    """Minimal response object for --fixture (no live HTTP)."""

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


class FixtureSession:
    """Session that always returns a local JSON fixture."""

    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def get(self, url: str, timeout: float | None = None, headers: dict | None = None):
        del url, timeout, headers
        return FixtureResponse(self.payload)


def load_json_list(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path}: catalog must be a JSON array")
    return payload


def load_company_names(path: Path, key: str) -> set[str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {item["name"] for item in payload.get(key, [])}


def scrape_and_merge(
    catalog_path: Path,
    *,
    fixture_path: Path | None = None,
    seen_on: str | None = None,
    rate_limit_delay: float = 1.0,
    artifact_path: Path | None = None,
    allowlist_path: Path = DEFAULT_ALLOWLIST,
    candidates_path: Path = DEFAULT_CANDIDATES,
) -> list[dict]:
    """Discover allowlisted scrapers, scrape, upsert by internship ID, and save."""
    if fixture_path is not None and Path(catalog_path).resolve() == DEFAULT_CATALOG.resolve():
        raise ValueError(
            "refusing to merge --fixture into the production catalog "
            "(data/active/internships.json); pass --catalog to a temp file"
        )
    seen = seen_on or date.today().isoformat()
    existing = load_json_list(catalog_path)
    allowlist = load_company_names(allowlist_path, "companies")
    candidates = load_company_names(candidates_path, "candidates")
    session = None
    delay = rate_limit_delay
    if fixture_path is not None:
        session = FixtureSession(json.loads(Path(fixture_path).read_text(encoding="utf-8")))
        delay = 0
    merged = existing
    for company, scraper_cls in discover_scrapers().items():
        if company not in allowlist or company in candidates:
            continue
        if fixture_path is not None and company != "Boston Scientific":
            continue
        scraper = scraper_cls(
            session=session,
            rate_limit_delay=delay,
            artifact_path=artifact_path,
        )
        result = scraper.scrape(seen_on=seen)
        if result.blocked:
            continue
        merged = upsert_catalog(merged, result.postings, seen_on=seen)
    output = Path(catalog_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return merged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Local Eightfold/PCSX JSON to merge without live HTTP",
    )
    parser.add_argument("--seen-on", default=None)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args(argv)
    scrape_and_merge(
        catalog_path=args.catalog,
        fixture_path=args.fixture,
        seen_on=args.seen_on,
        artifact_path=args.artifact,
    )
    return run_validation(args.catalog, DEFAULT_ARCHIVED, DEFAULT_SCHEMA)


if __name__ == "__main__":
    sys.exit(main())
