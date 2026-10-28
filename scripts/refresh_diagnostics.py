"""Export bounded diagnostic projections, never raw scraped text or exceptions."""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path
from uuid import UUID


def diagnostics_path(artifact_path: Path) -> Path:
    return artifact_path.with_name(artifact_path.stem + "-diagnostics")


def write_diagnostics(artifact_path: Path, progress: dict, candidates: list[Path]) -> None:
    """Only export safe types and known fields; raw candidate files stay private."""
    output = diagnostics_path(artifact_path)
    output.mkdir(parents=True, exist_ok=True)
    previews = {}
    identifiers = set()
    for name, path in zip(("active", "archived"), candidates[:2]):
        safe_rows = []
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(rows, list):
                rows = []
            for row in rows[:10000]:
                if not isinstance(row, dict):
                    continue
                try:
                    identifier = str(UUID(str(row.get("id", ""))))
                except ValueError:
                    continue
                identifiers.add(identifier)
                safe = {"id": identifier}
                if row.get("row_kind") in ("posting", "program_fallback"):
                    safe["row_kind"] = row["row_kind"]
                for field in ("first_seen", "last_seen", "closed_at", "last_miss_on"):
                    try:
                        safe[field] = date.fromisoformat(row[field]).isoformat()
                    except (KeyError, ValueError, TypeError):
                        pass
                safe_rows.append(safe)
        except (OSError, ValueError):
            pass
        previews[name] = safe_rows
    sha = os.environ.get("GITHUB_SHA", "")
    report = {
        "phase": progress["phase"],
        "attempted_sweep": progress["today"],
        "commit": sha if re.fullmatch(r"[0-9a-f]{40}", sha) else None,
        "candidate_status": "not_published",
        "catalog_validation_passed": progress.get("validated", False),
        "validation_error_count": progress.get("validation_error_count", 0),
        "validation_reasons": progress.get("validation_reasons", []),
        "implicated_ids": progress.get("validation_ids", []),
        "candidate_ids": sorted(identifiers),
        "failed_scrapers": progress.get("failed_scrapers", []),
        "recovery": "Rerun with the same output destinations; retain publication journals if recovery fails.",
        "preview_policy": "IDs, row kinds and dates only; raw text, URLs, errors and environment excluded.",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "candidate-preview.json").write_text(
        json.dumps(previews, indent=2) + "\n", encoding="utf-8"
    )
