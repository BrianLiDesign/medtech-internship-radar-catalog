#!/usr/bin/env python3
"""Validate internship catalog JSON against the schema."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.json"
DEFAULT_ACTIVE = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"


class CatalogValidationError(ValueError):
    """Carry validation evidence across pipeline stages without losing phase."""

    def __init__(self, errors: list[str], *, phase: str):
        super().__init__("; ".join(errors))
        self.errors = errors
        self.phase = phase


def validation_summary(errors: list[str]) -> dict:
    """Project errors to safe categories and IDs, excluding raw source text."""
    categories = {
        "duplicate id ": "duplicate_id",
        "active/archive overlap:": "overlapping_id",
        "closure metadata is not allowed": "active_closure_metadata",
        "valid closure metadata is required": "archived_closure_metadata",
    }
    return {
        "validation_error_count": len(errors),
        "validation_ids": sorted(
            set(re.findall(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", "\n".join(errors)))
        ),
        "validation_reasons": sorted(
            {
                next(
                    (code for text, code in categories.items() if text in error), "schema_or_input"
                )
                for error in errors
            }
        ),
    }


def validate_catalog_file(path: Path, schema: dict) -> list[str]:
    """Return validation error messages for one catalog JSON file."""
    catalog_path = Path(path)
    with catalog_path.open(encoding="utf-8") as handle:
        rows = json.load(handle)
    return validate_rows(rows, schema, str(catalog_path))


def validate_rows(rows: object, schema: dict, label: str) -> list[str]:
    """Validate an input catalog before any keyed conversion or mutation."""
    if not isinstance(rows, list):
        return [f"{label}: catalog must be a JSON array"]
    validator = Draft7Validator(schema)
    errors = []
    seen_ids = set()
    for index, row in enumerate(rows):
        for error in validator.iter_errors(row):
            errors.append(f"{label}[{index}]: {error.message}")
        row_id = row.get("id") if isinstance(row, dict) else None
        if isinstance(row_id, str) and row_id:
            if row_id in seen_ids:
                errors.append(f"{label}[{index}]: duplicate id {row_id}")
            else:
                seen_ids.add(row_id)
    return errors


def validate_catalogs(
    active_path: Path, archived_path: Path, schema: dict, *, phase: str = "final"
) -> list[str]:
    """Validate active and archived catalog files."""
    errors = []
    errors.extend(validate_catalog_file(active_path, schema))
    errors.extend(validate_catalog_file(archived_path, schema))
    if phase not in {"input", "final"}:
        raise ValueError("validation phase must be input or final")
    if errors or phase == "input":
        return errors
    active = json.loads(Path(active_path).read_text(encoding="utf-8"))
    archived = json.loads(Path(archived_path).read_text(encoding="utf-8"))
    overlap = {row["id"] for row in active} & {row["id"] for row in archived}
    errors.extend(f"active/archive overlap: {identifier}" for identifier in sorted(overlap))
    for row in active:
        if "closed_at" in row or "close_reason" in row:
            errors.append(f"active {row['id']}: closure metadata is not allowed")
    for row in archived:
        try:
            date.fromisoformat(row.get("closed_at", ""))
            if row.get("close_reason") not in {
                "ats_closed",
                "consecutive_misses",
                "force_close",
                "url_dead",
            }:
                raise ValueError("missing closure reason")
        except (ValueError, TypeError):
            errors.append(f"archived {row['id']}: valid closure metadata is required")
    return errors


def run_validation(
    active_path: Path = DEFAULT_ACTIVE,
    archived_path: Path = DEFAULT_ARCHIVED,
    schema_path: Path = DEFAULT_SCHEMA,
    *,
    phase: str = "final",
) -> int:
    """Validate catalogs and print results. Return 0 on success, 1 on failure."""
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    try:
        errors = validate_catalogs(active_path, archived_path, schema, phase=phase)
    except (OSError, ValueError) as exc:
        errors = [f"catalog input could not be read ({type(exc).__name__})"]
    return report_validation(errors)


def report_validation(errors: list[str]) -> int:
    """Print and return a single validation result shared with diagnostics."""
    if errors:
        print(f"[FAIL] Catalog validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  {error}")
        return 1
    print("[PASS] Catalog validation passed.")
    return 0


def main() -> int:
    return run_validation()


if __name__ == "__main__":
    sys.exit(main())
