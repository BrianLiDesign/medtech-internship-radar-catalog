# AGENTS.md

Instructions for AI coding agents working on the MedTech Internship Radar Catalog.

## Project overview

Public, evergreen data catalog of **US STEM internships** (and summer-shaped co-ops) at allowlisted medtech / diabetes device companies. Python 3.9+ scrapers populate `data/active/internships.json`. JSON Schema validates all records. GitHub Actions runs CI and daily refresh PRs.

Read [PLAN.md](PLAN.md) and [CURRENT-SLICE](docs/pm/CURRENT-SLICE.md) before choosing work.
The approved scope is 32 companies, default season `summer-2027`. HANDOFF.md
preserves the historical 12-company decisions and acceptance, superseded by approved
waves. Read [CONTEXT.md](CONTEXT.md) for terms; when changing ingestion or archive
behavior, read [ELIGIBILITY](docs/ELIGIBILITY.md) and [AUTOMATION](docs/AUTOMATION.md).
Dated coverage and verification limits are in [verification evidence](docs/verification/2026-10-19-documentation.md).

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

## Commands

```bash
make lint      # Ruff + compileall
make format    # Ruff fix + format
make test      # pytest
make validate  # schema validation
make e2e       # mocked refresh + module CLI tests using temporary outputs
```

If `make` is unavailable (typical on Windows PowerShell):

```bash
python -m ruff check scripts tests config/scrapers
python -m ruff format --check scripts tests config/scrapers
python -m compileall -q scripts config/scrapers
python -m pytest -q
python -m scripts.validate_data
```

## Code style

- Python 3.9 compatible syntax
- Ruff for linting and formatting
- Type hints where they clarify interfaces
- Scraper logic in `config/scrapers/`; shared utilities in `scripts/`

## Boundaries — do not

- Hand-edit `data/active/internships.json` or `data/archived/internships.json` in contributor PRs
- Commit secrets, cookies, API keys, or `.env` files
- Bypass schema validation before saving catalog data
- Change internship IDs for existing records without an explicit migration plan
- Import program scrapers or the program schema from `student-program-radar-catalog`
- Mention Student Program Radar in **public** README or student-facing docs (separate brand)
- Filter v1 listings by visa/sponsorship
- Add allowlist companies beyond the current wave without an explicit scope change
- Create a new git repo per season — `season` is a field; `config/current_season.json` is the README default
- Build the website (`medtech-internship-radar`) in this repo
- Use live network in CI; mock HTTP

## Scraper development

1. Subclass the internship base scraper in `config/scrapers/<company>_scraper.py`
2. Implement discovery + parse into schema-compliant **posting** rows; apply the shared eligibility gate to every parsed posting; the refresh pipeline restores approved fallback seeds when appropriate (scrapers return postings, not invented fallback rows)
3. Register via `<Company>Scraper` naming convention
4. Add company to `config/allowlist.json` only when in scope
5. Test with mocked HTTP
6. Prefer Greenhouse/Lever/stable JSON; do not block coverage on reverse-engineering Workday
7. Internship IDs are UUID v5 from `scripts/internship_ids.py` — never hardcode arbitrary IDs

## Security

- Treat scraped HTML as untrusted input
- Use framework rate limiting and timeouts
- Report vulnerabilities via GitHub private security advisories ([SECURITY.md](SECURITY.md))

## Pull requests

- Run `make lint test validate e2e` before submitting
- Scraper PRs must not include generated catalog data changes; use automation refresh or a separate reviewed maintainer cleanup PR.
- Change README content in `scripts/generate_dashboard.py` and regenerate all three views.
- Use repository-root `python -m scripts.*` commands; no PYTHONPATH override or editable install is needed.

## Pattern repo (internal only)

`student-program-radar-catalog` is a **skeleton reference** (allowlist, schema gate, generated README, daily refresh-via-PR, dual license). Copy habits, not ambassador scrapers, program `role_type`, or a 60-day program SLO.
