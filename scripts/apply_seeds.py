#!/usr/bin/env python3
"""Apply maintainer program-fallback seeds into the active catalog.

Reads seed *input* (not a hand-edited README), assigns internship IDs, and
merges schema-complete rows into data/active/internships.json. Existing
posting rows (for example Boston Scientific scrape results) are kept.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from internship_ids import canonical_apply_url, internship_id
from validate_data import run_validation

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEEDS = REPO_ROOT / "config" / "seeds" / "program_fallbacks.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_SEASON_FILE = REPO_ROOT / "config" / "current_season.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.json"

REQUIRED_SEED_FIELDS = ("company", "title", "apply_url", "program_url", "location")


def load_seed_document(path: Path) -> dict:
    """Load a seed document with a `seeds` array."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("seeds"), list):
        raise ValueError(f"{path}: seed file must be an object with a seeds array")
    return payload


def _current_season(season_path: Path) -> str:
    payload = json.loads(season_path.read_text(encoding="utf-8"))
    return payload["season"]


def row_from_seed(seed: dict, *, season: str, seen_on: str) -> dict:
    """Map one seed object to a schema-complete program_fallback row."""
    missing = [field for field in REQUIRED_SEED_FIELDS if not str(seed.get(field, "")).strip()]
    if missing:
        company = seed.get("company", "<unknown>")
        raise ValueError(f"seed for {company} is missing required field(s): {', '.join(missing)}")
    apply_url = seed["apply_url"].strip()
    program_url = seed["program_url"].strip()
    row = {
        "id": "",
        "company": seed["company"].strip(),
        "title": seed["title"].strip(),
        "apply_url": apply_url,
        "season": str(seed.get("season") or season),
        "role_family": seed.get("role_family") or "Other STEM",
        "location": seed["location"].strip(),
        "degree": seed.get("degree") or "unspecified",
        "row_kind": "program_fallback",
        "source": "seed",
        "first_seen": seed.get("first_seen") or seen_on,
        "last_seen": seed.get("last_seen") or seen_on,
        "work_auth": seed.get("work_auth") or "unspecified",
        "eligibility": seed.get("eligibility") or "open",
        "miss_count": int(seed.get("miss_count", 0)),
        "canonical_apply_url": canonical_apply_url(apply_url),
        "program_url": program_url,
        "ats": seed.get("ats") or "unknown",
        "short_description": seed.get("short_description") or "",
    }
    row["id"] = internship_id(row)
    return row


def load_existing_catalog(path: Path) -> list[dict]:
    """Load an existing catalog array, or [] if the file is missing."""
    output = Path(path)
    if not output.exists():
        return []
    payload = json.loads(output.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path}: catalog must be a JSON array")
    return payload


def merge_seeds_with_existing(seed_rows: list[dict], existing: list[dict]) -> list[dict]:
    """Replace program-fallback seeds; keep posting rows (e.g. Boston Scientific).

    Companies that already have posting rows do not get a new program_fallback.
    """
    seed_companies = {row["company"] for row in seed_rows}
    posting_companies = {row["company"] for row in existing if row.get("row_kind") == "posting"}
    kept = [
        row
        for row in existing
        if row.get("row_kind") != "program_fallback" or row.get("company") not in seed_companies
    ]
    new_seeds = [row for row in seed_rows if row["company"] not in posting_companies]
    return new_seeds + kept


def ensure_program_fallbacks(catalog: list[dict], seed_rows: list[dict]) -> list[dict]:
    """Add seed fallbacks for companies that have no active catalog row.

    Does not rewrite existing fallbacks (first_seen stays frozen).
    """
    covered = {row["company"] for row in catalog}
    extra = [dict(row) for row in seed_rows if row["company"] not in covered]
    return catalog + extra


def restore_missing_fallbacks(
    catalog_path: Path,
    seed_path: Path = DEFAULT_SEEDS,
    *,
    season_path: Path = DEFAULT_SEASON_FILE,
    seen_on: str | None = None,
) -> list[dict]:
    """Write seed fallbacks for companies that dropped to zero active rows."""
    document = load_seed_document(seed_path)
    season = document.get("season") or _current_season(season_path)
    seen = seen_on or document.get("first_seen") or date.today().isoformat()
    seed_rows = [row_from_seed(seed, season=season, seen_on=seen) for seed in document["seeds"]]
    output = Path(catalog_path)
    restored = ensure_program_fallbacks(load_existing_catalog(output), seed_rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(restored, indent=2) + "\n", encoding="utf-8")
    return restored


def apply_seeds(
    seed_path: Path,
    output_path: Path,
    *,
    season_path: Path = DEFAULT_SEASON_FILE,
    seen_on: str | None = None,
) -> list[dict]:
    """Merge program_fallback rows from seed input. Return the written rows."""
    document = load_seed_document(seed_path)
    season = document.get("season") or _current_season(season_path)
    seen = seen_on or document.get("first_seen") or date.today().isoformat()
    seed_rows = [row_from_seed(seed, season=season, seen_on=seen) for seed in document["seeds"]]
    output = Path(output_path)
    rows = merge_seeds_with_existing(seed_rows, load_existing_catalog(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--season-file", type=Path, default=DEFAULT_SEASON_FILE)
    args = parser.parse_args(argv)
    apply_seeds(args.seeds, args.output, season_path=args.season_file)
    return run_validation(args.output, DEFAULT_ARCHIVED, DEFAULT_SCHEMA)


if __name__ == "__main__":
    sys.exit(main())
