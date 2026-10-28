"""Refresh and archive safety contracts, observed through persisted outputs."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.refresh_catalog import refresh_catalog
from scripts.validate_data import validate_catalogs

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "data/schema.json").read_text(encoding="utf-8"))


@pytest.fixture
def outputs(tmp_path):
    paths = {
        name: tmp_path / name
        for name in (
            "catalog_path",
            "archived_path",
            "health_path",
            "readme_path",
            "inactive_path",
            "newest_path",
            "artifact_path",
        )
    }
    paths["catalog_path"].write_text("[]", encoding="utf-8")
    paths["archived_path"].write_text("[]", encoding="utf-8")
    for name in ("health_path", "readme_path", "inactive_path", "newest_path"):
        paths[name].write_text("previous published snapshot", encoding="utf-8")
    fixture_map = tmp_path / "map.json"
    fixture_map.write_text("{}", encoding="utf-8")
    paths["fixture_map_path"] = fixture_map
    return paths


def row(**changes):
    record = json.loads((ROOT / "tests/fixtures/example_internships.json").read_text())[0]
    record.update(changes)
    return record


def snapshot(outputs):
    return {
        path: path.read_bytes() if path.exists() else None
        for name, path in outputs.items()
        if name not in ("artifact_path", "fixture_map_path")
    }


@pytest.mark.parametrize("invalid", ["overlap", "active_closed", "archive_open"])
def test_final_validation_rejects_inconsistent_states(tmp_path, invalid):
    active, archived = tmp_path / "active.json", tmp_path / "archived.json"
    opened = row()
    closed = row(closed_at="2026-08-14", close_reason="ats_closed")
    active.write_text(
        json.dumps(
            [closed if invalid == "active_closed" else opened] if invalid != "archive_open" else []
        )
    )
    archived.write_text(
        json.dumps(
            [closed if invalid == "overlap" else opened] if invalid != "active_closed" else []
        )
    )
    assert validate_catalogs(active, archived, SCHEMA)


@pytest.mark.parametrize("which", ["catalog_path", "archived_path"])
def test_refresh_rejects_conflicting_input_without_writes(outputs, which, capsys):
    first = (
        row(closed_at="2026-08-14", close_reason="ats_closed")
        if which == "archived_path"
        else row()
    )
    outputs[which].write_text(json.dumps([first, dict(first, title="Conflicting title")]))
    before = snapshot(outputs)
    assert refresh_catalog(**outputs, today="2026-08-15") == 1
    assert snapshot(outputs) == before
    assert first["id"] in capsys.readouterr().out


def test_generation_failure_preserves_published_snapshot(outputs, monkeypatch):
    import scripts.refresh_catalog as refresh

    def broken_generation(**kwargs):
        kwargs["readme_path"].write_text("partial candidate")
        raise OSError("injected generation failure")

    monkeypatch.setattr(refresh, "write_readme", broken_generation)
    before = snapshot(outputs)
    assert refresh_catalog(**outputs, today="2026-08-15") == 1
    assert snapshot(outputs) == before


@pytest.mark.parametrize("failure", ["replacement", "interruption", "rollback"])
@pytest.mark.parametrize("originally_absent", [False, True])
def test_publication_failure_and_restart_recover_snapshot(
    outputs, monkeypatch, failure, originally_absent
):
    import scripts.refresh_catalog as refresh
    from scripts.catalog_publication import journal_path

    if originally_absent:
        outputs["catalog_path"].unlink()
    before = snapshot(outputs)
    replace = os.replace
    target = outputs["archived_path"].resolve()
    tripped = False

    def fail_replace(source, destination):
        nonlocal tripped
        if Path(destination) == target and (not tripped or failure == "rollback"):
            tripped = True
            if failure == "interruption":
                raise KeyboardInterrupt("process interrupted")
            raise OSError("disk replacement failed")
        return replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_replace)
    if failure == "interruption":
        with pytest.raises(KeyboardInterrupt):
            refresh_catalog(**outputs, today="2026-08-15")
    else:
        assert refresh_catalog(**outputs, today="2026-08-15") == 1
    if failure == "replacement":
        assert snapshot(outputs) == before
    else:
        assert journal_path(outputs["catalog_path"]).exists()
    monkeypatch.setattr(os, "replace", replace)

    def failed_next_generation(**kwargs):
        raise OSError("next sweep failed after recovery")

    monkeypatch.setattr(refresh, "write_readme", failed_next_generation)
    assert refresh_catalog(**outputs, today="2026-08-16") == 1
    assert snapshot(outputs) == before
    assert not journal_path(outputs["catalog_path"]).exists()


@pytest.mark.parametrize("failure", ["duplicates", "overlap", "repeat"])
def test_archive_cli_validates_persisted_catalog_pair(tmp_path, failure):
    active, archived = tmp_path / "active.json", tmp_path / "archived.json"
    record = row()
    active.write_text(
        json.dumps(
            [record, dict(record, title="Conflicting title")]
            if failure == "duplicates"
            else [record]
        )
    )
    archived.write_text(
        json.dumps(
            [
                dict(
                    record,
                    first_seen="2026-01-01",
                    closed_at="2026-08-01",
                    close_reason="ats_closed",
                )
            ]
            if failure == "overlap"
            else []
        )
    )
    before = (active.read_bytes(), archived.read_bytes())
    command = [
        sys.executable,
        "-m",
        "scripts.archive_closed",
        "--active",
        str(active),
        "--archived",
        str(archived),
        "--today",
        "2026-08-15",
        "--force-close",
        record["id"],
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if failure == "duplicates":
        assert result.returncode != 0
        assert record["id"] in result.stdout + result.stderr
        assert (active.read_bytes(), archived.read_bytes()) == before
    else:
        assert result.returncode == 0, result.stderr
        assert validate_catalogs(active, archived, SCHEMA) == []
        assert len(json.loads(archived.read_text())) == 1
        assert json.loads(archived.read_text())[0]["first_seen"] == (
            "2026-01-01" if failure == "overlap" else record["first_seen"]
        )
        after = (active.read_bytes(), archived.read_bytes())
        assert subprocess.run(command, cwd=ROOT, capture_output=True).returncode == 0
        assert (active.read_bytes(), archived.read_bytes()) == after


def test_archive_cli_rejects_invalid_final_state_without_writes(tmp_path):
    active, archived = tmp_path / "active.json", tmp_path / "archived.json"
    active.write_text("[]")
    archived.write_text(json.dumps([row()]))
    before = archived.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.archive_closed",
            "--active",
            str(active),
            "--archived",
            str(archived),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert archived.read_bytes() == before


def test_failure_diagnostics_do_not_export_untrusted_text(outputs, monkeypatch):
    import scripts.refresh_catalog as refresh

    secret = "fixture-only-password-DO-NOT-EXPORT"

    def broken_generation(**kwargs):
        raise OSError(f"Authorization: Bearer {secret}")

    monkeypatch.setattr(refresh, "write_readme", broken_generation)
    before = snapshot(outputs)
    assert refresh_catalog(**outputs, today="2026-08-15") == 1
    report_path = (
        outputs["artifact_path"].with_name(outputs["artifact_path"].stem + "-diagnostics")
        / "report.json"
    )
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["phase"] == "generation"
    assert report["attempted_sweep"] == "2026-08-15"
    assert report["candidate_status"] == "not_published"
    assert secret not in report_path.read_text()
    assert snapshot(outputs) == before


def test_input_validation_permits_reconcilable_overlap(outputs):
    opened = row(first_seen="2026-08-14", last_seen="2026-08-15")
    closed = dict(
        opened, first_seen="2026-01-01", closed_at="2026-08-01", close_reason="force_close"
    )
    outputs["catalog_path"].write_text(json.dumps([opened]))
    outputs["archived_path"].write_text(json.dumps([closed]))
    assert (
        validate_catalogs(outputs["catalog_path"], outputs["archived_path"], SCHEMA, phase="input")
        == []
    )
    assert refresh_catalog(**outputs, today="2026-08-15") == 0
    assert validate_catalogs(outputs["catalog_path"], outputs["archived_path"], SCHEMA) == []
    reopened = next(
        item
        for item in json.loads(outputs["catalog_path"].read_text())
        if item["id"] == opened["id"]
    )
    assert reopened["first_seen"] == "2026-01-01"
    assert "closed_at" not in reopened


def test_archive_cli_recovers_interrupted_promotion_before_next_sweep(tmp_path):
    active, archived = tmp_path / "active.json", tmp_path / "archived.json"
    record = row()
    active.write_text(json.dumps([record]))
    archived.write_text("[]")
    args = [
        "--active",
        str(active),
        "--archived",
        str(archived),
        "--today",
        "2026-08-15",
        "--force-close",
        record["id"],
    ]
    launcher = """
import os, sys, runpy
from pathlib import Path
target = Path(sys.argv.pop(1)).resolve()
original = os.replace
def interrupted(source, destination):
    if Path(destination) == target:
        raise KeyboardInterrupt('injected interruption')
    return original(source, destination)
os.replace = interrupted
sys.argv[0] = 'scripts.archive_closed'
runpy.run_module('scripts.archive_closed', run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-c", launcher, str(archived), *args], cwd=ROOT, capture_output=True
    )
    assert result.returncode != 0
    result = subprocess.run(
        [sys.executable, "-m", "scripts.archive_closed", *args], cwd=ROOT, capture_output=True
    )
    assert result.returncode == 0, result.stderr
    assert validate_catalogs(active, archived, SCHEMA) == []
    assert json.loads(active.read_text()) == []
    closed = json.loads(archived.read_text())
    assert len(closed) == 1
    assert closed[0]["id"] == record["id"]
    assert closed[0]["first_seen"] == record["first_seen"]


def test_failed_candidate_validation_preserves_snapshot_and_reports_ids(outputs, monkeypatch):
    import scripts.refresh_catalog as refresh

    def invalid_candidates(*args, **kwargs):
        Path(args[1]).write_text(json.dumps([row()]))

    monkeypatch.setattr(refresh, "archive_catalog_files", invalid_candidates)
    before = snapshot(outputs)
    assert refresh_catalog(**outputs, today="2026-08-15") == 1
    assert snapshot(outputs) == before
    diagnostic_dir = outputs["artifact_path"].with_name(
        outputs["artifact_path"].stem + "-diagnostics"
    )
    report = json.loads((diagnostic_dir / "report.json").read_text())
    assert report["phase"] == "final_validation"
    assert report["validation_error_count"] >= 1
    assert row()["id"] in report["implicated_ids"]


def test_staging_write_failure_preserves_snapshot(outputs, monkeypatch):
    original = Path.write_text

    def failed_health_write(path, content, *args, **kwargs):
        if '"last_sweep"' in content:
            raise OSError("injected staging write failure")
        return original(path, content, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", failed_health_write)
    before = snapshot(outputs)
    assert refresh_catalog(**outputs, today="2026-08-15") == 1
    assert snapshot(outputs) == before


def test_existing_invalid_archive_exports_safe_validation_reason(outputs):
    outputs["archived_path"].write_text(json.dumps([row()]))
    before = snapshot(outputs)
    assert refresh_catalog(**outputs, today="2026-08-15") == 1
    diagnostic_dir = outputs["artifact_path"].with_name(
        outputs["artifact_path"].stem + "-diagnostics"
    )
    report = json.loads((diagnostic_dir / "report.json").read_text())
    assert report["phase"] == "final_validation"
    assert report["validation_error_count"] == 1
    assert row()["id"] in report["implicated_ids"]
    assert "archived_closure_metadata" in report["validation_reasons"]
    assert snapshot(outputs) == before


def test_refresh_uses_supplied_schema_through_archiving(outputs, tmp_path):
    custom = dict(SCHEMA)
    custom["properties"] = dict(custom["properties"], fixture_marker={"type": "string"})
    schema_path = tmp_path / "custom-schema.json"
    schema_path.write_text(json.dumps(custom))
    outputs["catalog_path"].write_text(
        json.dumps([row(fixture_marker="preserve-me", last_seen="2026-08-15")])
    )
    assert refresh_catalog(**outputs, today="2026-08-15", schema_path=schema_path) == 0
    kept = next(
        item
        for item in json.loads(outputs["catalog_path"].read_text())
        if item["id"] == row()["id"]
    )
    assert kept["fixture_marker"] == "preserve-me"
