"""Maintainer merge of structured issues into the catalog (no live network)."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator

from internship_ids import internship_id
from merge_issue import MergeIssueError, merge_issue, merge_issue_row, row_from_issue
from validate_data import validate_catalog_file

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((REPO_ROOT / "data" / "schema.json").read_text(encoding="utf-8"))
ALLOWLIST = REPO_ROOT / "config" / "allowlist.json"
CANDIDATES = REPO_ROOT / "config" / "candidates.json"

V1_COMPANIES = (
    "Medtronic",
    "Intuitive",
    "Abbott",
    "Dexcom",
    "Insulet",
    "Tandem",
    "Stryker",
    "Boston Scientific",
    "Edwards",
    "BD",
    "Zimmer Biomet",
    "GE HealthCare",
)

ISSUE_FIELDS = {
    "company": "Medtronic",
    "title": "Software Engineer Intern",
    "location": "Minneapolis, MN",
    "apply_url": "https://jobs.example.com/intern?utm_source=radar",
    "degree": "Unspecified",
    "season": "summer-2027",
    "req_id": "R-12345",
}


def _allowlist_names() -> tuple[str, ...]:
    payload = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    return tuple(company["name"] for company in payload["companies"])


def _empty_catalogs(tmp_path: Path) -> tuple[Path, Path]:
    active = tmp_path / "active.json"
    archived = tmp_path / "archived.json"
    active.write_text("[]\n", encoding="utf-8")
    archived.write_text("[]\n", encoding="utf-8")
    return active, archived


def test_issue_row_sets_source_issue_and_stable_id():
    row = row_from_issue(
        ISSUE_FIELDS,
        seen_on="2026-08-14",
        allowlist_names=V1_COMPANIES,
    )
    assert row["source"] == "issue"
    assert row["row_kind"] == "posting"
    assert row["degree"] == "unspecified"
    assert row["role_family"] == "Software"
    assert row["id"] == internship_id(row)
    again = row_from_issue(
        ISSUE_FIELDS,
        seen_on="2026-08-20",
        allowlist_names=V1_COMPANIES,
    )
    assert again["id"] == row["id"]
    errors = list(Draft7Validator(SCHEMA).iter_errors(row))
    assert errors == [], errors


def test_req_id_identity_is_stable_when_url_changes():
    first = row_from_issue(
        ISSUE_FIELDS,
        seen_on="2026-08-14",
        allowlist_names=V1_COMPANIES,
    )
    shifted = dict(ISSUE_FIELDS)
    shifted["apply_url"] = "https://jobs.example.com/other-path"
    second = row_from_issue(
        shifted,
        seen_on="2026-08-14",
        allowlist_names=V1_COMPANIES,
    )
    assert first["id"] == second["id"]
    assert first["id"] == internship_id({"company": "Medtronic", "req_id": "R-12345"})


def test_merge_skips_duplicate_ids_in_active_and_archived():
    row = row_from_issue(
        ISSUE_FIELDS,
        seen_on="2026-08-14",
        allowlist_names=V1_COMPANIES,
    )
    added, status = merge_issue_row([], row, archived=[])
    assert status == "added"
    assert len(added) == 1
    again, dup_status = merge_issue_row(added, row, archived=[])
    assert dup_status == "duplicate"
    assert again == added
    archived_dup, archived_status = merge_issue_row([], row, archived=[row])
    assert archived_status == "duplicate"
    assert archived_dup == []


def test_merge_issue_writes_once_and_validates(tmp_path):
    active, archived = _empty_catalogs(tmp_path)
    row, status = merge_issue(
        ISSUE_FIELDS,
        active,
        archived,
        allowlist_path=ALLOWLIST,
        candidates_path=CANDIDATES,
        seen_on="2026-08-14",
    )
    assert status == "added"
    written = json.loads(active.read_text(encoding="utf-8"))
    assert written == [row]
    assert validate_catalog_file(active, SCHEMA) == []
    _, duplicate = merge_issue(
        ISSUE_FIELDS,
        active,
        archived,
        allowlist_path=ALLOWLIST,
        candidates_path=CANDIDATES,
        seen_on="2026-08-14",
    )
    assert duplicate == "duplicate"
    assert json.loads(active.read_text(encoding="utf-8")) == [row]


def test_candidate_company_is_rejected():
    fields = dict(ISSUE_FIELDS)
    fields["company"] = "Parked Device Co"
    try:
        row_from_issue(
            fields,
            seen_on="2026-08-14",
            allowlist_names=_allowlist_names(),
            candidate_names=("Parked Device Co",),
        )
    except MergeIssueError as exc:
        assert "candidate" in str(exc).lower()
    else:
        raise AssertionError("expected MergeIssueError for candidate company")


def test_unknown_company_is_rejected():
    fields = dict(ISSUE_FIELDS)
    fields["company"] = "Not A Device Co"
    try:
        row_from_issue(
            fields,
            seen_on="2026-08-14",
            allowlist_names=V1_COMPANIES,
        )
    except MergeIssueError as exc:
        assert "allowlist" in str(exc).lower()
    else:
        raise AssertionError("expected MergeIssueError for unknown company")
