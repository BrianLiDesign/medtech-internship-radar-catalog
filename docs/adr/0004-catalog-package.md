# ADR-0004: Catalog package for shared I/O

## Status

Accepted (2026-09-13)

## Context

Pipeline modules duplicated JSON load/save helpers and `ROLE_FAMILIES`. The architecture review flagged shallow I/O modules with poor locality.

## Decision

Introduce a top-level `catalog/` package with:

- `catalog.io` — `load_json_list`, `write_json_list`, `current_season`
- `catalog.schema_constants` — `ROLE_FAMILIES`

`scripts/` remains the CLI entry-point layer. Scrapers stay in `config/scrapers/` with `scripts/` adapters until a later migration moves them under `catalog.scrapers`.

## Consequences

- `pyproject.toml` adds the repo root to `pythonpath` so `catalog` imports work in tests and scripts.
- A full rename of `scripts/` → `catalog.pipeline` is deferred; this ADR records the seam without a disruptive move.
