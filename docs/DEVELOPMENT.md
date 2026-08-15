# Development Guide

Local setup, tests, and workflows for the MedTech Internship Radar Catalog.

## Prerequisites

- Python 3.9 or newer
- Git
- No live network required for CI or `make test` / `make e2e`

## Setup

```bash
git clone <this-repo>
cd medtech-internship-radar-catalog
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
```

## Common commands

```bash
make lint      # Ruff + compileall
make format    # Ruff fix + format
make test      # pytest
make validate  # schema validation
make e2e       # fixture dry-run: scrape → validate → archive → generate README
```

If `make` is unavailable (typical on Windows PowerShell):

```bash
python -m ruff check scripts tests config/scrapers
python -m ruff format --check scripts tests config/scrapers
python -m compileall -q scripts config/scrapers
python -m pytest -q
python scripts/validate_data.py
python scripts/refresh_catalog.py --fixture tests/fixtures/boston_scientific_pcsx.json
```

## Project layout

| Path | Purpose |
|------|---------|
| `data/active/internships.json` | Published active catalog (automation / maintainer only) |
| `data/archived/internships.json` | Archived rows |
| `data/schema.json` | JSON Schema for internship rows |
| `config/allowlist.json` | v1 companies approved for scraping and README coverage |
| `config/candidates.json` | Employers parked for a later allowlist |
| `config/current_season.json` | README default season (`summer-2027` for v1) |
| `config/scrapers/` | Company scrapers (`<Company>Scraper`) |
| `scripts/` | IDs, validate, generator, scrape, archive, issue merge |
| `docs/` | Schema, automation, development, ADRs |

## Development rules

1. **Do not hand-edit** `data/active/internships.json` or
   `data/archived/internships.json` in contributor PRs. Catalog updates come from
   scrapers, seeds, `scripts/merge_issue.py`, or maintainer review of refresh PRs.
2. **Preserve stable internship IDs.** IDs are UUID v5 values from
   `scripts/internship_ids.py`. Do not change an existing `id` without a
   migration plan.
3. **Mock HTTP in tests.** CI must not hit live ATS endpoints.
4. **Run** `make lint test validate` (and `make e2e` when scraper/refresh
   behavior changes) before opening a pull request.
5. **Never commit secrets**, session cookies, or credentials.
6. **Do not hand-edit README tables.** `scripts/generate_dashboard.py` owns them.

## Adding a scraper

See [SCRAPER_CHECKLIST.md](SCRAPER_CHECKLIST.md). New employers start in
`config/candidates.json`, then the allowlist, then a scraper — see
[CONTRIBUTING.md](../CONTRIBUTING.md).

v1 does **not** require reverse-engineering Workday. Greenhouse, Lever, or other
stable JSON is enough; Workday companies can remain on a program-fallback row.

## Merging an issue into the catalog

Maintainers only. Documented in [CONTRIBUTING.md](../CONTRIBUTING.md):

```bash
python scripts/merge_issue.py --dry-run --company "..." --title "..." \
  --location "..." --apply-url "https://..." --degree Unspecified --season summer-2027
python scripts/validate_data.py
python scripts/generate_dashboard.py
```

## Troubleshooting

- **Import errors from `scripts/`:** run commands from the repository root.
  `python scripts/*.py` puts `scripts/` on `sys.path`.
- **Stale README:** regenerate with `python scripts/generate_dashboard.py`.
- **Fixture dry-run:** `python scripts/refresh_catalog.py --fixture tests/fixtures/boston_scientific_pcsx.json`

## Related docs

- [CONTRIBUTING.md](../CONTRIBUTING.md) — issues for reqs; PRs for scrapers/allowlist
- [AUTOMATION.md](AUTOMATION.md) — daily refresh via PR
- [SCHEMA.md](SCHEMA.md) — internship record shape
- [AGENTS.md](../AGENTS.md) — agent instructions
