# Development Guide

Local setup, tests, and workflows for the MedTech Internship Radar Catalog.

## Prerequisites

- Python 3.9 or newer
- Git
- No live network required for CI or `make test` / `make e2e`

## Setup

```bash
git clone https://github.com/BrianLiDesign/medtech-internship-radar-catalog.git
cd medtech-internship-radar-catalog
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

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
make e2e       # mocked refresh + module CLI tests, with temporary outputs
```

If `make` is unavailable (typical on Windows PowerShell):

```bash
python -m ruff check scripts tests config/scrapers
python -m ruff format --check scripts tests config/scrapers
python -m compileall -q scripts config/scrapers
python -m pytest -q
python -m scripts.validate_data
python -m pytest tests/test_refresh_catalog.py tests/test_refresh_safety.py tests/test_cli.py tests/test_qualification_refresh.py -q
```

## Project layout

| Path | Purpose |
|------|---------|
| `data/active/internships.json` | Published active catalog (automation / maintainer only) |
| `data/archived/internships.json` | Archived rows |
| `data/schema.json` | JSON Schema for internship rows |
| `config/allowlist.json` | Current 32 approved companies; original v1 was 12 |
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
4. **Run** `make lint test validate e2e` (or the Python equivalents above) before
   opening a pull request.
5. **Never commit secrets**, session cookies, or credentials.
6. **Do not hand-edit README tables.** `scripts/generate_dashboard.py` owns them.

## Adding a scraper

Shared inclusion rules, adapter evidence, missing-information policy, and the
reviewed cleanup path are documented in [ELIGIBILITY.md](ELIGIBILITY.md).

See [SCRAPER_CHECKLIST.md](SCRAPER_CHECKLIST.md). New employers start in
`config/candidates.json`, then the allowlist, then a scraper — see
[CONTRIBUTING.md](../CONTRIBUTING.md).

The approved scope is 32 companies and the default season is `summer-2027`.
Registration and mocked adapter tests do not certify live coverage; see the
[dated verification record](verification/2026-10-19-documentation.md).

Coverage does **not** require reverse-engineering Workday. Greenhouse, Lever, or other
stable JSON is enough; Workday companies can remain on a program-fallback row.

## Module commands and generated files

Run from the repository root. Use `python -m scripts.<command>`; no editable
install or `PYTHONPATH` override is needed. The command handoff is implemented in
[PR #14](https://github.com/BrianLiDesign/medtech-internship-radar-catalog/pull/14).
`make e2e` is exactly the targeted pytest command shown above, not a live scrape.
It exercises fixture refresh and module entrypoints in temporary outputs.

For README wording/layout, edit `scripts/generate_dashboard.py` and run
`python -m scripts.generate_dashboard`. It writes `README.md`, `README-Newest.md`,
and `README-Inactive.md` from the existing catalogs; it does not refresh listings.
Setup installs require package access; local tests and fixture refresh use mocked HTTP.
See [dated command verification](verification/2026-10-19-documentation.md).

## Merging an issue into the catalog

Maintainers only. Documented in [CONTRIBUTING.md](../CONTRIBUTING.md):

```bash
python -m scripts.merge_issue --dry-run --company "..." --title "..." \
  --location "..." --apply-url "https://..." --degree Unspecified --season summer-2027
python -m scripts.validate_data
python -m scripts.generate_dashboard
```

The example is a preview only. Remove `--dry-run` only for a reviewed maintainer
change, validate and regenerate, then submit a PR. `merge_issue` validates identity
and schema; maintainers must independently review eligibility.

## Troubleshooting

- **Import errors from `scripts/`:** run commands from the repository root.
  Use `python -m scripts.<command>` so both `scripts` and `catalog` resolve from
  the checkout. No editable install or `PYTHONPATH` override is needed.
- **Stale README:** regenerate with `python -m scripts.generate_dashboard`.
- **Fixture dry-run:** `python -m pytest tests/test_refresh_catalog.py tests/test_refresh_safety.py tests/test_cli.py tests/test_qualification_refresh.py -q` (`--fixture` must not write `data/active/internships.json`)

## Related docs

- [CONTRIBUTING.md](../CONTRIBUTING.md) — issues for reqs; PRs for scrapers/allowlist
- [AUTOMATION.md](AUTOMATION.md) — daily refresh via PR
- [SCHEMA.md](SCHEMA.md) — internship record shape
- [AGENTS.md](../AGENTS.md) — agent instructions
