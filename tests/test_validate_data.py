"""Catalog JSON schema gate."""

import json
import subprocess
import sys
from pathlib import Path

from validate_data import run_validation, validate_catalog_file, validate_catalogs

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"
REPO_ROOT = Path(__file__).resolve().parents[1]


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def valid_posting(**overrides):
    row = {
        "id": "11111111-1111-4111-8111-111111111111",
        "company": "Medtronic",
        "title": "Software Intern",
        "apply_url": "https://jobs.example.com/software-intern",
        "season": "summer-2027",
        "role_family": "Software",
        "location": "Minneapolis, MN",
        "degree": "bs",
        "row_kind": "posting",
        "source": "seed",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    row.update(overrides)
    return row


def test_empty_catalog_is_valid(tmp_path):
    catalog = tmp_path / "internships.json"
    catalog.write_text("[]", encoding="utf-8")
    errors = validate_catalog_file(catalog, schema={})
    assert errors == []


def test_validates_active_and_archived_catalog_paths(tmp_path):
    active = tmp_path / "active.json"
    archived = tmp_path / "archived.json"
    active.write_text("[]", encoding="utf-8")
    archived.write_text("[]", encoding="utf-8")
    errors = validate_catalogs(active, archived, schema={})
    assert errors == []


def test_missing_apply_url_is_rejected(tmp_path):
    row = valid_posting()
    del row["apply_url"]
    catalog = tmp_path / "internships.json"
    catalog.write_text(json.dumps([row]), encoding="utf-8")
    errors = validate_catalog_file(catalog, load_schema())
    assert errors
    assert any("apply_url" in error for error in errors)


def test_bad_role_family_enum_is_rejected(tmp_path):
    catalog = tmp_path / "internships.json"
    catalog.write_text(json.dumps([valid_posting(role_family="Marketing")]), encoding="utf-8")
    errors = validate_catalog_file(catalog, load_schema())
    assert errors
    assert any("role_family" in error or "Marketing" in error for error in errors)


def test_duplicate_id_is_rejected(tmp_path):
    first = valid_posting()
    second = valid_posting(title="Firmware Intern", location="Boston, MA")
    catalog = tmp_path / "internships.json"
    catalog.write_text(json.dumps([first, second]), encoding="utf-8")
    errors = validate_catalog_file(catalog, load_schema())
    assert errors
    assert any("duplicate" in error.lower() for error in errors)


def test_archived_catalog_schema_errors_are_reported(tmp_path):
    active = tmp_path / "active.json"
    archived = tmp_path / "archived.json"
    active.write_text("[]", encoding="utf-8")
    archived.write_text(json.dumps([valid_posting(degree="phd")]), encoding="utf-8")
    errors = validate_catalogs(active, archived, load_schema())
    assert errors
    assert any("phd" in error or "degree" in error for error in errors)


def test_example_posting_and_program_fallback_fixture_is_valid():
    fixture = Path(__file__).resolve().parent / "fixtures" / "example_internships.json"
    errors = validate_catalog_file(fixture, load_schema())
    assert errors == []
    rows = json.loads(fixture.read_text(encoding="utf-8"))
    kinds = {row["row_kind"] for row in rows}
    assert kinds == {"posting", "program_fallback"}


def test_validate_script_exits_zero_on_empty_repo_catalogs():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_data.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed" in result.stdout.lower()


def test_run_validation_exits_nonzero_on_invalid_catalog(tmp_path):
    active = tmp_path / "active.json"
    archived = tmp_path / "archived.json"
    active.write_text(json.dumps([valid_posting(degree="phd")]), encoding="utf-8")
    archived.write_text("[]", encoding="utf-8")
    assert run_validation(active, archived, SCHEMA_PATH) == 1
