"""Publish validated file sets with recoverable replacement and rollback."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path


def atomic_write(path: Path, content: bytes) -> None:
    """Replace one file using a temporary sibling on the same filesystem."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def journal_path(anchor: Path) -> Path:
    return anchor.resolve().with_name(f".{anchor.name}.publication")


def recover_publication(destinations: list[Path]) -> None:
    """Restore an interrupted snapshot before any new work on its destinations."""
    targets = [path.resolve() for path in destinations]
    journal = journal_path(targets[0])
    if not journal.exists():
        return
    manifest = journal / "manifest.json"
    if not manifest.exists():
        # No destination is changed until the complete manifest is installed.
        shutil.rmtree(journal)
        return
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload["destinations"] != [str(path) for path in targets]:
        raise ValueError(f"recovery requires the original output destinations; retain {journal}")
    if payload["state"] == "prepared":
        # Check all backups before restoring any destination. A damaged journal
        # must remain available for manual recovery rather than partially reset.
        for index, existed in enumerate(payload["existed"]):
            if existed and not (journal / f"{index}.backup").is_file():
                raise ValueError(f"publication backup missing; retain {journal}")
        for index, target in enumerate(targets):
            if payload["existed"][index]:
                atomic_write(target, (journal / f"{index}.backup").read_bytes())
            else:
                target.unlink(missing_ok=True)
        payload["state"] = "rolled_back"
        atomic_write(manifest, json.dumps(payload).encode("utf-8"))
    elif payload["state"] not in {"committed", "rolled_back"}:
        raise ValueError(f"unknown publication state; retain {journal}")
    shutil.rmtree(journal)


def publish_files(candidates: list[Path], destinations: list[Path]) -> None:
    """Promote a complete candidate set; retain evidence if rollback fails."""
    targets = [path.resolve() for path in destinations]
    if len(set(targets)) != len(targets) or len(candidates) != len(targets):
        raise ValueError("publication requires distinct destinations and a complete candidate set")
    for candidate in candidates:
        if not candidate.is_file():
            raise ValueError("publication candidate is missing")
    recover_publication(targets)
    journal = journal_path(targets[0])
    journal.mkdir(parents=True)
    existed = [target.exists() for target in targets]
    for index, target in enumerate(targets):
        if existed[index]:
            shutil.copyfile(target, journal / f"{index}.backup")
    payload = {
        "destinations": [str(path) for path in targets],
        "existed": existed,
        "state": "prepared",
    }
    manifest = journal / "manifest.json"
    atomic_write(manifest, json.dumps(payload).encode("utf-8"))
    try:
        for candidate, target in zip(candidates, targets):
            atomic_write(target, candidate.read_bytes())
        payload["state"] = "committed"
        atomic_write(manifest, json.dumps(payload).encode("utf-8"))
    except Exception:
        # A failed rollback deliberately leaves backups and manifest in place.
        recover_publication(targets)
        raise
    recover_publication(targets)
