"""Catalog file I/O and season reads."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEASON_FILE = REPO_ROOT / "config" / "current_season.json"


def load_json_list(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path}: catalog must be a JSON array")
    return payload


def write_json_list(path: Path, rows: list[dict]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def current_season(path: Path = DEFAULT_SEASON_FILE) -> str:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload["season"]
