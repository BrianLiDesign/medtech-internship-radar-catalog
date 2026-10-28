#!/usr/bin/env python3
"""Archive closed internship rows after ATS-closed, two misses, or force-close."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from scripts.catalog_publication import publish_files, recover_publication
from scripts.validate_data import (
    DEFAULT_SCHEMA,
    CatalogValidationError,
    validate_catalogs,
    validate_rows,
)

CLOSE_REASON_ATS = "ats_closed"
CLOSE_REASON_MISSES = "consecutive_misses"
CLOSE_REASON_FORCE = "force_close"
CLOSE_REASON_URL = "url_dead"
DEAD_URL_STATUSES = frozenset({404, 410})
ATS_CLOSED_MARKERS = ("no longer accepting applications",)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ACTIVE = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"
PROBE_TIMEOUT = 15.0


@dataclass
class Observation:
    """Liveness signal for one internship row on a sweep."""

    seen: bool = False
    ats_closed: bool = False
    url_status: int | None = None


def probe_url(session: object | None, url: str) -> tuple[int | None, str]:
    """Return (HTTP status, body) for a URL, or (None, "") if it cannot be probed."""
    if session is None or not url:
        return None, ""
    try:
        response = session.get(url, timeout=PROBE_TIMEOUT, allow_redirects=True)
    except Exception:
        return None, ""
    status = getattr(response, "status_code", None)
    text = getattr(response, "text", "") or ""
    return status, text


def probe_url_status(session: object | None, url: str) -> int | None:
    """Return HTTP status for a URL, or None if it cannot be probed."""
    status, _body = probe_url(session, url)
    return status


def looks_ats_closed(*, status: int | None, body: str) -> bool:
    """True when an apply URL is gone or the ATS page says the req is closed."""
    if status in DEAD_URL_STATUSES:
        return True
    text = body.lower()
    return any(marker in text for marker in ATS_CLOSED_MARKERS)


def record_daily_miss(row: dict, today: str) -> None:
    """Count at most once per day, requiring adjacent dates for a streak.

    Legacy undated counts cannot establish a previous daily failure.
    """
    previous = row.get("last_miss_on")
    if previous and previous >= today:
        return
    yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
    row["miss_count"] = int(row.get("miss_count") or 0) + 1 if previous == yesterday else 1
    row["last_miss_on"] = today


def observation_for_row(
    row: dict,
    *,
    today: str,
    signals: dict[str, Observation],
    session: object | None,
) -> Observation:
    if row["id"] in signals:
        return signals[row["id"]]
    url = row.get("program_url") or row.get("apply_url") or ""
    if row.get("row_kind") == "program_fallback":
        return Observation(seen=True, url_status=probe_url_status(session, url))
    status, body = probe_url(session, row.get("apply_url") or "")
    return Observation(
        seen=row.get("last_seen") == today,
        ats_closed=looks_ats_closed(status=status, body=body) if session is not None else False,
        url_status=status,
    )


def apply_archive_rules(
    active: list[dict],
    archived: list[dict],
    *,
    today: str,
    observations: dict[str, Observation] | None = None,
    force_close_ids: list[str] | None = None,
    session: object | None = None,
    unavailable_companies: set[str] | None = None,
    schema: dict | None = None,
) -> tuple[list[dict], list[dict]]:
    """Return still-active rows and the archived catalog including new closes."""
    forced = set(force_close_ids or [])
    schema = (
        schema if schema is not None else json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
    )
    errors = validate_rows(active, schema, "active") + validate_rows(archived, schema, "archived")
    if errors:
        raise CatalogValidationError(errors, phase="input")
    still_active: list[dict] = []
    archived_by_id = {row["id"]: row for row in archived}
    signals = observations or {}
    unavailable = unavailable_companies or set()
    for row in active:
        updated = dict(row)
        is_fallback = updated.get("row_kind") == "program_fallback"
        previous = archived_by_id.get(row["id"])
        if previous is not None:
            # Rediscovered postings retain their identity and original discovery
            # date. Closed fallback hubs require explicit maintainer reopening.
            if is_fallback:
                continue
            updated["first_seen"] = min(previous["first_seen"], updated["first_seen"])
            del archived_by_id[row["id"]]
        updated.pop("closed_at", None)
        updated.pop("close_reason", None)
        signal = observation_for_row(row, today=today, signals=signals, session=session)
        if row["id"] in forced:
            updated["closed_at"] = today
            updated["close_reason"] = CLOSE_REASON_FORCE
            archived_by_id[row["id"]] = updated
            continue
        if signal.ats_closed or (not is_fallback and signal.url_status in DEAD_URL_STATUSES):
            updated["closed_at"] = today
            updated["close_reason"] = CLOSE_REASON_ATS
            archived_by_id[row["id"]] = updated
            continue
        url_dead = signal.url_status in DEAD_URL_STATUSES
        if is_fallback:
            if url_dead:
                record_daily_miss(updated, today)
                if int(updated["miss_count"]) >= 2:
                    updated["closed_at"] = today
                    updated["close_reason"] = CLOSE_REASON_URL
                    archived_by_id[row["id"]] = updated
                    continue
            elif signal.url_status is not None and 200 <= signal.url_status < 300:
                updated["miss_count"] = 0
                updated.pop("last_miss_on", None)
            # Timeouts, rate limits, redirects without a final response, and
            # other inconclusive results neither add a miss nor prove health.
            still_active.append(updated)
            continue
        if updated.get("company") in unavailable:
            # A failed company scrape is not evidence that its postings closed.
            # Preserve the previous miss count unless a definitive close signal
            # above proved otherwise.
            still_active.append(updated)
            continue
        if not signal.seen:
            record_daily_miss(updated, today)
        else:
            updated["miss_count"] = 0
            updated.pop("last_miss_on", None)
        if int(updated.get("miss_count") or 0) >= 2:
            updated["closed_at"] = today
            updated["close_reason"] = CLOSE_REASON_MISSES
            archived_by_id[row["id"]] = updated
            continue
        still_active.append(updated)
    return still_active, list(archived_by_id.values())


def load_catalog(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path}: catalog must be a JSON array")
    return payload


def write_catalog(path: Path, rows: list[dict]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def archive_catalog_files(
    active_path: Path = DEFAULT_ACTIVE,
    archived_path: Path = DEFAULT_ARCHIVED,
    *,
    today: str | None = None,
    force_close_ids: list[str] | None = None,
    session: object | None = None,
    unavailable_companies: set[str] | None = None,
    schema_path: Path = DEFAULT_SCHEMA,
) -> tuple[list[dict], list[dict]]:
    """Load catalogs, apply archive rules, and write both files."""
    sweep_day = today or date.today().isoformat()
    destinations = [Path(active_path), Path(archived_path)]
    recover_publication(destinations)
    active = load_catalog(active_path)
    archived = load_catalog(archived_path) if Path(archived_path).exists() else []
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    new_active, new_archived = apply_archive_rules(
        active,
        archived,
        today=sweep_day,
        force_close_ids=force_close_ids,
        session=session,
        unavailable_companies=unavailable_companies,
        schema=schema,
    )
    with tempfile.TemporaryDirectory(prefix="catalog-archive-") as temporary:
        candidates = [Path(temporary) / "active.json", Path(temporary) / "archived.json"]
        write_catalog(candidates[0], new_active)
        write_catalog(candidates[1], new_archived)
        errors = validate_catalogs(*candidates, schema)
        if errors:
            raise CatalogValidationError(errors, phase="final")
        publish_files(candidates, destinations)
    return new_active, new_archived


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", type=Path, default=DEFAULT_ACTIVE)
    parser.add_argument("--archived", type=Path, default=DEFAULT_ARCHIVED)
    parser.add_argument("--today", default=None)
    parser.add_argument(
        "--force-close",
        action="append",
        default=[],
        help="Internship ID to force-close (repeatable)",
    )
    args = parser.parse_args(argv)
    archive_catalog_files(
        args.active,
        args.archived,
        today=args.today,
        force_close_ids=args.force_close or None,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
