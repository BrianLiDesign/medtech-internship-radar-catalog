#!/usr/bin/env python3
"""Merge a structured internship issue into the active catalog.

Maintainer-only. Assigns a stable internship ID, sets source: issue, and
refuses duplicate IDs. Community PRs must not edit listings JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from internship_ids import canonical_apply_url, internship_id
from scraper_framework import role_family_for_title
from validate_data import run_validation

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ACTIVE = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.json"
DEFAULT_ALLOWLIST = REPO_ROOT / "config" / "allowlist.json"
DEFAULT_SEASON_FILE = REPO_ROOT / "config" / "current_season.json"
DEFAULT_CANDIDATES = REPO_ROOT / "config" / "candidates.json"

DEGREE_ALIASES = {
    "bs": "bs",
    "bachelor's": "bs",
    "bachelors": "bs",
    "bachelor": "bs",
    "ms": "ms",
    "master's": "ms",
    "masters": "ms",
    "master": "ms",
    "bs/ms": "bs_ms",
    "bs_ms": "bs_ms",
    "unspecified": "unspecified",
}

ROLE_FAMILIES = (
    "Software",
    "BME/R&D",
    "Electrical/firmware",
    "Mechanical/robotics",
    "Data/ML",
    "Quality/manufacturing",
    "Other STEM",
)


class MergeIssueError(ValueError):
    """Invalid issue fields or a company that is not on the v1 allowlist."""


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def allowlist_company_names(allowlist_path: Path = DEFAULT_ALLOWLIST) -> tuple[str, ...]:
    payload = load_json(allowlist_path)
    return tuple(company["name"] for company in payload["companies"])


def candidate_company_names(candidates_path: Path = DEFAULT_CANDIDATES) -> tuple[str, ...]:
    payload = load_json(candidates_path)
    return tuple(candidate["name"] for candidate in payload["candidates"])


def normalize_degree(value: str) -> str:
    key = str(value).strip().lower()
    if key not in DEGREE_ALIASES:
        raise MergeIssueError(f"unknown degree {value!r}; use Unspecified, BS, MS, or BS/MS")
    return DEGREE_ALIASES[key]


def _current_season(season_path: Path) -> str:
    return load_json(season_path)["season"]


def row_from_issue(
    fields: dict,
    *,
    seen_on: str,
    allowlist_names: tuple[str, ...],
    candidate_names: tuple[str, ...] = (),
) -> dict:
    """Map issue fields to a schema-complete posting row with source: issue."""
    company = str(fields.get("company") or "").strip()
    if not company:
        raise MergeIssueError("company is required")
    if company not in allowlist_names:
        if company in candidate_names:
            raise MergeIssueError(f"{company} is a candidate, not a v1 allowlist company")
        raise MergeIssueError(f"{company} is not on the v1 allowlist")

    title = str(fields.get("title") or "").strip()
    location = str(fields.get("location") or "").strip()
    apply_url = str(fields.get("apply_url") or "").strip()
    if not title:
        raise MergeIssueError("title is required")
    if not location:
        raise MergeIssueError("location is required")
    if not apply_url:
        raise MergeIssueError("apply_url is required")

    season = str(fields.get("season") or "").strip()
    if not season:
        raise MergeIssueError("season is required")
    degree = normalize_degree(fields.get("degree") or "unspecified")
    role_family = str(fields.get("role_family") or "").strip() or role_family_for_title(title)
    if role_family not in ROLE_FAMILIES:
        raise MergeIssueError(f"unknown role_family {role_family!r}")

    row = {
        "id": "",
        "company": company,
        "title": title,
        "apply_url": apply_url,
        "season": season,
        "role_family": role_family,
        "location": location,
        "degree": degree,
        "row_kind": "posting",
        "source": "issue",
        "first_seen": seen_on,
        "last_seen": seen_on,
        "work_auth": "unspecified",
        "eligibility": "open",
        "miss_count": 0,
        "canonical_apply_url": canonical_apply_url(apply_url),
    }
    req_id = str(fields.get("req_id") or "").strip()
    if req_id:
        row["req_id"] = req_id
    row["id"] = internship_id(row)
    return row


def merge_issue_row(
    active: list[dict],
    row: dict,
    archived: list[dict] | None = None,
) -> tuple[list[dict], str]:
    """Insert row unless its id already exists. Returns (catalog, status)."""
    known = {item["id"] for item in active}
    known.update(item["id"] for item in (archived or []) if item.get("id"))
    if row["id"] in known:
        return list(active), "duplicate"
    return list(active) + [row], "added"


def merge_issue(
    fields: dict,
    active_path: Path,
    archived_path: Path,
    *,
    allowlist_path: Path = DEFAULT_ALLOWLIST,
    candidates_path: Path = DEFAULT_CANDIDATES,
    season_path: Path = DEFAULT_SEASON_FILE,
    seen_on: str | None = None,
    dry_run: bool = False,
) -> tuple[dict, str]:
    """Build and optionally write an issue row. Returns (row, status)."""
    allowlist_names = allowlist_company_names(allowlist_path)
    candidate_names = ()
    if Path(candidates_path).exists():
        candidate_names = candidate_company_names(candidates_path)
    payload = dict(fields)
    if not str(payload.get("season") or "").strip():
        payload["season"] = _current_season(season_path)
    seen = seen_on or date.today().isoformat()
    row = row_from_issue(
        payload,
        seen_on=seen,
        allowlist_names=allowlist_names,
        candidate_names=candidate_names,
    )
    active = load_json(active_path)
    archived = load_json(archived_path) if Path(archived_path).exists() else []
    if not isinstance(active, list):
        raise MergeIssueError(f"{active_path}: catalog must be a JSON array")
    merged, status = merge_issue_row(active, row, archived=archived)
    if dry_run or status != "added":
        return row, status
    Path(active_path).write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return row, status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--apply-url", required=True)
    parser.add_argument("--degree", default="Unspecified")
    parser.add_argument("--season", default="")
    parser.add_argument("--req-id", default="")
    parser.add_argument("--role-family", default="")
    parser.add_argument("--seen-on", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--active", type=Path, default=DEFAULT_ACTIVE)
    parser.add_argument("--archived", type=Path, default=DEFAULT_ARCHIVED)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--season-file", type=Path, default=DEFAULT_SEASON_FILE)
    args = parser.parse_args(argv)
    fields = {
        "company": args.company,
        "title": args.title,
        "location": args.location,
        "apply_url": args.apply_url,
        "degree": args.degree,
        "season": args.season,
        "req_id": args.req_id,
        "role_family": args.role_family,
    }
    try:
        row, status = merge_issue(
            fields,
            args.active,
            args.archived,
            allowlist_path=args.allowlist,
            candidates_path=args.candidates,
            season_path=args.season_file,
            seen_on=args.seen_on or None,
            dry_run=args.dry_run,
        )
    except MergeIssueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": status, "row": row}, indent=2))
    if args.dry_run or status != "added":
        return 0
    return run_validation(args.active, args.archived, DEFAULT_SCHEMA)


if __name__ == "__main__":
    sys.exit(main())
