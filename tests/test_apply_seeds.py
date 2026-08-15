"""Maintainer program-fallback seeds → catalog rows (no live network)."""

import json
from pathlib import Path

from jsonschema import Draft7Validator

from apply_seeds import (
    apply_seeds,
    ensure_program_fallbacks,
    load_seed_document,
    merge_seeds_with_existing,
    restore_missing_fallbacks,
)
from internship_ids import internship_id
from validate_data import validate_catalog_file

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "data" / "schema.json"
FIXTURE_SEEDS = Path(__file__).resolve().parent / "fixtures" / "program_fallbacks.json"
PRODUCTION_SEEDS = REPO_ROOT / "config" / "seeds" / "program_fallbacks.json"
ALLOWLIST_PATH = REPO_ROOT / "config" / "allowlist.json"

REQUIRED_FIELDS = (
    "id",
    "company",
    "title",
    "apply_url",
    "season",
    "role_family",
    "location",
    "degree",
    "row_kind",
    "source",
    "first_seen",
    "last_seen",
)

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

WAVE1_COMPANIES = (
    "J&J MedTech",
    "Siemens Healthineers",
    "Philips",
    "Penumbra",
    "Align",
)

WAVE2_COMPANIES = (
    "Smith+Nephew",
    "Baxter",
    "ResMed",
    "Hologic",
    "Teleflex",
    "Integra LifeSciences",
    "Globus Medical",
    "Arthrex",
    "STERIS",
    "CONMED",
    "Olympus",
    "CooperCompanies",
    "Biotronik",
    "Alcon",
    "Inspire Medical",
)

ALLOWLIST_COMPANIES = V1_COMPANIES + WAVE1_COMPANIES + WAVE2_COMPANIES


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_fixture_seeds_emit_two_program_fallback_rows_with_apply_urls(tmp_path):
    output = tmp_path / "internships.json"
    rows = apply_seeds(FIXTURE_SEEDS, output)
    assert len(rows) == 2
    assert all(row["apply_url"] for row in rows)
    assert {row["company"] for row in rows} == {"Medtronic", "Intuitive"}
    assert all(row["row_kind"] == "program_fallback" for row in rows)
    assert all(row["source"] == "seed" for row in rows)
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written == rows


def test_seed_rows_include_every_required_schema_field(tmp_path):
    rows = apply_seeds(FIXTURE_SEEDS, tmp_path / "internships.json")
    schema = load_schema()
    for row in rows:
        for field in REQUIRED_FIELDS:
            assert field in row, f"missing required field {field}"
        errors = list(Draft7Validator(schema).iter_errors(row))
        assert errors == [], errors


def test_internship_ids_are_stable_across_applies(tmp_path):
    first = apply_seeds(FIXTURE_SEEDS, tmp_path / "first.json")
    second = apply_seeds(FIXTURE_SEEDS, tmp_path / "second.json")
    assert [row["id"] for row in first] == [row["id"] for row in second]
    for row in first:
        assert row["id"] == internship_id(row)


def test_program_fallback_identity_uses_company_and_program_url(tmp_path):
    rows = apply_seeds(FIXTURE_SEEDS, tmp_path / "internships.json")
    medtronic = next(row for row in rows if row["company"] == "Medtronic")
    expected = internship_id(
        {
            "company": "Medtronic",
            "row_kind": "program_fallback",
            "program_url": "https://example.test/medtronic/interns",
            "apply_url": "https://example.test/other",
        }
    )
    assert medtronic["id"] == expected
    assert medtronic["canonical_apply_url"] == "https://example.test/medtronic/interns"


def test_seed_without_apply_url_is_rejected(tmp_path):
    bad = {
        "season": "summer-2027",
        "first_seen": "2026-08-14",
        "seeds": [
            {
                "company": "Medtronic",
                "title": "University internships",
                "apply_url": "",
                "program_url": "https://example.test/medtronic/interns",
                "location": "Minneapolis, MN",
            }
        ],
    }
    seed_path = tmp_path / "bad.json"
    seed_path.write_text(json.dumps(bad), encoding="utf-8")
    try:
        apply_seeds(seed_path, tmp_path / "out.json")
    except ValueError as exc:
        assert "apply_url" in str(exc)
    else:
        raise AssertionError("expected ValueError for empty apply_url")


def test_production_seeds_emit_thirty_two_valid_rows_with_stable_ids(tmp_path):
    output = tmp_path / "internships.json"
    rows = apply_seeds(PRODUCTION_SEEDS, output)
    assert [row["company"] for row in rows] == list(ALLOWLIST_COMPANIES)
    assert len(rows) == 32
    assert all(row["apply_url"].startswith("https://") for row in rows)
    assert all(row["program_url"].startswith("https://") for row in rows)
    assert all(row["degree"] == "unspecified" for row in rows)
    assert all(row["role_family"] == "Other STEM" for row in rows)
    assert all(row["season"] == "summer-2027" for row in rows)
    assert all(row["source"] == "seed" for row in rows)
    assert all(row["row_kind"] == "program_fallback" for row in rows)
    assert validate_catalog_file(output, load_schema()) == []
    second = apply_seeds(PRODUCTION_SEEDS, tmp_path / "again.json")
    assert [row["id"] for row in rows] == [row["id"] for row in second]
    allowlist_names = {
        company["name"]
        for company in json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))["companies"]
    }
    assert {row["company"] for row in rows} == allowlist_names
    assert set(WAVE1_COMPANIES) <= {row["company"] for row in rows}
    assert set(WAVE2_COMPANIES) <= {row["company"] for row in rows}


def test_apply_seeds_keeps_existing_posting_rows(tmp_path):
    posting = {
        "id": "keep-me",
        "company": "Boston Scientific",
        "title": "Software Engineer Intern",
        "apply_url": "https://bostonscientific.eightfold.ai/careers/job/1",
        "season": "summer-2027",
        "role_family": "Software",
        "location": "Marlborough, MA",
        "degree": "unspecified",
        "row_kind": "posting",
        "source": "scrape",
        "first_seen": "2026-08-14",
        "last_seen": "2026-08-14",
    }
    output = tmp_path / "internships.json"
    output.write_text(json.dumps([posting], indent=2) + "\n", encoding="utf-8")
    rows = apply_seeds(PRODUCTION_SEEDS, output)
    companies = [row["company"] for row in rows]
    assert "Boston Scientific" in companies
    bsc = [row for row in rows if row["company"] == "Boston Scientific"]
    assert all(row["row_kind"] == "posting" for row in bsc)
    assert all(row["source"] == "scrape" for row in bsc)
    assert posting in bsc
    fallbacks = [row for row in rows if row["row_kind"] == "program_fallback"]
    assert "Boston Scientific" not in {row["company"] for row in fallbacks}
    assert {row["company"] for row in fallbacks} == set(ALLOWLIST_COMPANIES) - {"Boston Scientific"}
    assert merge_seeds_with_existing([], [posting]) == [posting]


def test_load_seed_document_reads_local_fixture():
    document = load_seed_document(FIXTURE_SEEDS)
    assert len(document["seeds"]) == 2
    assert document["season"] == "summer-2027"


def test_ensure_program_fallbacks_restores_company_with_no_rows():
    medtronic = {
        "id": "keep-fallback",
        "company": "Medtronic",
        "title": "University internships",
        "apply_url": "https://www.medtronic.com/en-us/our-company/careers/early-careers.html",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-14",
    }
    bsc_seed = {
        "id": "bsc-fallback",
        "company": "Boston Scientific",
        "title": "Students and early careers",
        "apply_url": "https://www.bostonscientific.com/en-US/careers/students.html",
        "row_kind": "program_fallback",
        "first_seen": "2026-08-15",
    }
    medtronic_seed = dict(medtronic)
    medtronic_seed["first_seen"] = "2026-08-15"
    restored = ensure_program_fallbacks([medtronic], [medtronic_seed, bsc_seed])
    companies = {row["company"] for row in restored}
    assert companies == {"Medtronic", "Boston Scientific"}
    kept = next(row for row in restored if row["company"] == "Medtronic")
    assert kept["first_seen"] == "2026-08-14"
    assert kept["id"] == "keep-fallback"


def test_restore_missing_fallbacks_adds_boston_scientific(tmp_path):
    catalog = tmp_path / "internships.json"
    catalog.write_text(
        json.dumps(
            [
                {
                    "id": "keep-fallback",
                    "company": "Medtronic",
                    "title": "University internships",
                    "apply_url": "https://www.medtronic.com/en-us/our-company/careers/early-careers.html",
                    "row_kind": "program_fallback",
                    "first_seen": "2026-08-14",
                }
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rows = restore_missing_fallbacks(
        catalog,
        PRODUCTION_SEEDS,
        seen_on="2026-08-15",
    )
    assert "Boston Scientific" in {row["company"] for row in rows}
    written = json.loads(catalog.read_text(encoding="utf-8"))
    assert written == rows
    bsc = next(row for row in rows if row["company"] == "Boston Scientific")
    assert bsc["row_kind"] == "program_fallback"
    assert bsc["source"] == "seed"
