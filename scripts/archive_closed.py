#!/usr/bin/env python3
"""Archive closed internship rows after ATS-closed, two misses, or force-close."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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
) -> tuple[list[dict], list[dict]]:
    """Return still-active rows and the archived catalog including new closes."""
    forced = set(force_close_ids or [])
    still_active: list[dict] = []
    newly_archived = list(archived)
    signals = observations or {}
    for row in active:
        updated = dict(row)
        signal = observation_for_row(row, today=today, signals=signals, session=session)
        if row["id"] in forced:
            updated["closed_at"] = today
            updated["close_reason"] = CLOSE_REASON_FORCE
            newly_archived.append(updated)
            continue
        if signal.ats_closed:
            updated["closed_at"] = today
            updated["close_reason"] = CLOSE_REASON_ATS
            newly_archived.append(updated)
            continue
        url_dead = signal.url_status in DEAD_URL_STATUSES
        is_fallback = updated.get("row_kind") == "program_fallback"
        if is_fallback:
            if url_dead:
                updated["miss_count"] = int(updated.get("miss_count") or 0) + 1
                if int(updated["miss_count"]) >= 2:
                    updated["closed_at"] = today
                    updated["close_reason"] = CLOSE_REASON_URL
                    newly_archived.append(updated)
                    continue
            still_active.append(updated)
            continue
        if not signal.seen:
            updated["miss_count"] = int(updated.get("miss_count") or 0) + 1
        else:
            updated["miss_count"] = 0
        if int(updated.get("miss_count") or 0) >= 2:
            updated["closed_at"] = today
            updated["close_reason"] = CLOSE_REASON_MISSES
            newly_archived.append(updated)
            continue
        still_active.append(updated)
    return still_active, newly_archived


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
) -> tuple[list[dict], list[dict]]:
    """Load catalogs, apply archive rules, and write both files."""
    sweep_day = today or date.today().isoformat()
    active = load_catalog(active_path)
    archived = load_catalog(archived_path) if Path(archived_path).exists() else []
    new_active, new_archived = apply_archive_rules(
        active,
        archived,
        today=sweep_day,
        force_close_ids=force_close_ids,
        session=session,
    )
    write_catalog(active_path, new_active)
    write_catalog(archived_path, new_archived)
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
