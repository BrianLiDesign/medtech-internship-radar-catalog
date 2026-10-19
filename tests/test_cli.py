"""Exercise command entry points without pytest's interpreter or import paths."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.validate_data import validate_catalogs

REPO_ROOT = Path(__file__).resolve().parents[1]


def cli_env():
    return {key: value for key, value in os.environ.items() if key.upper() != "PYTHONPATH"}


@pytest.mark.parametrize(
    "command",
    ["refresh_catalog", "scrape_internships", "apply_seeds", "merge_issue", "archive_closed"],
)
def test_module_help_without_pythonpath(command):
    result = subprocess.run(
        [sys.executable, "-m", f"scripts.{command}", "--help"],
        cwd=REPO_ROOT,
        env=cli_env(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "usage:" in result.stdout


@pytest.mark.parametrize("guard_network", [False, True], ids=["module-cli", "network-guard"])
def test_refresh_cli_fixture_without_pythonpath_or_network(tmp_path, guard_network):
    outputs = {
        "catalog": tmp_path / "active.json",
        "archived": tmp_path / "archived.json",
        "health": tmp_path / "health.json",
        "artifact": tmp_path / "scrape_failures.json",
        "readme": tmp_path / "README.md",
        "inactive": tmp_path / "README-Inactive.md",
        "newest": tmp_path / "README-Newest.md",
    }
    # Every production output must stay byte-for-byte unchanged, including logs.
    production = [
        REPO_ROOT / "data/active/internships.json",
        REPO_ROOT / "data/archived/internships.json",
        REPO_ROOT / "data/health.json",
        REPO_ROOT / "logs/scrape_failures.json",
        *(REPO_ROOT / name for name in ("README.md", "README-Inactive.md", "README-Newest.md")),
    ]
    before = {path: path.read_bytes() if path.exists() else None for path in production}
    stale = json.loads(
        (REPO_ROOT / "tests/fixtures/example_internships.json").read_text(encoding="utf-8")
    )[0]
    stale.update(last_seen="2026-08-13", miss_count=1)
    outputs["catalog"].write_text(json.dumps([stale]), encoding="utf-8")
    outputs["archived"].write_text("[]\n", encoding="utf-8")
    args = [
        "--fixture",
        str(REPO_ROOT / "tests/fixtures/boston_scientific_pcsx.json"),
        "--today",
        "2026-08-14",
    ]
    for option, path in outputs.items():
        args.extend([f"--{option}", str(path)])
    # run_module executes the same __main__ entry point as -m, while allowing
    # a network tripwire inside the child. No pytest imports or path injection.
    launcher = """
import runpy
import sys
def deny_network(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
        raise AssertionError("live network is forbidden in the fixture CLI")
sys.addaudithook(deny_network)
sys.argv = ["scripts.refresh_catalog", *sys.argv[1:]]
runpy.run_module("scripts.refresh_catalog", run_name="__main__")
"""
    invocation = ["-c", launcher] if guard_network else ["-m", "scripts.refresh_catalog"]
    result = subprocess.run(
        [sys.executable, *invocation, *args],
        cwd=REPO_ROOT,
        env=cli_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert all(path.exists() for path in outputs.values())
    schema = json.loads((REPO_ROOT / "data/schema.json").read_text(encoding="utf-8"))
    assert validate_catalogs(outputs["catalog"], outputs["archived"], schema) == []
    active = json.loads(outputs["catalog"].read_text(encoding="utf-8"))
    assert any(
        row["company"] == "Boston Scientific" and row["row_kind"] == "posting" for row in active
    )
    health = json.loads(outputs["health"].read_text(encoding="utf-8"))
    assert health["last_sweep"] == "2026-08-14"
    assert health["updated_count"] > 0
    assert health["failed_scrapers"] == []
    assert health["archived_count"] == 1
    archived = json.loads(outputs["archived"].read_text(encoding="utf-8"))
    assert archived[0]["id"] == stale["id"]
    assert archived[0]["close_reason"] == "consecutive_misses"
    assert json.loads(outputs["artifact"].read_text(encoding="utf-8")) == []
    for name in ("readme", "newest"):
        assert "Boston Scientific" in outputs[name].read_text(encoding="utf-8")
    assert stale["title"] in outputs["inactive"].read_text(encoding="utf-8")
    assert {path: path.read_bytes() if path.exists() else None for path in production} == before
