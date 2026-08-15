#!/usr/bin/env python3
"""Validate internship catalog JSON against the schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.json"
DEFAULT_ACTIVE = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"


def validate_catalog_file(path: Path, schema: dict) -> list[str]:
    """Return validation error messages for one catalog JSON file."""
    catalog_path = Path(path)
    with catalog_path.open(encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        return [f"{catalog_path}: catalog must be a JSON array"]
    validator = Draft7Validator(schema)
    errors = []
    seen_ids = set()
    for index, row in enumerate(rows):
        for error in validator.iter_errors(row):
            errors.append(f"{catalog_path}[{index}]: {error.message}")
        row_id = row.get("id") if isinstance(row, dict) else None
        if row_id:
            if row_id in seen_ids:
                errors.append(f"{catalog_path}[{index}]: duplicate id {row_id}")
            else:
                seen_ids.add(row_id)
    return errors


def validate_catalogs(active_path: Path, archived_path: Path, schema: dict) -> list[str]:
    """Validate active and archived catalog files."""
    errors = []
    errors.extend(validate_catalog_file(active_path, schema))
    errors.extend(validate_catalog_file(archived_path, schema))
    return errors


def run_validation(
    active_path: Path = DEFAULT_ACTIVE,
    archived_path: Path = DEFAULT_ARCHIVED,
    schema_path: Path = DEFAULT_SCHEMA,
) -> int:
    """Validate catalogs and print results. Return 0 on success, 1 on failure."""
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    errors = validate_catalogs(active_path, archived_path, schema)
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
