# Contributing

Thank you for helping keep this US STEM internship catalog accurate.

## Who may edit listings JSON

`data/active/internships.json` and `data/archived/internships.json` are
**automation- and maintainer-owned**. Community pull requests must not edit those
files (including raw JSON dumps). The README tables are generated — do not
hand-edit them either.

## How to contribute

### 1. Suggest a req (structured issue)

Use the **Add internship** issue template for a posting at an allowlisted
company. Required fields: company, title, location, apply URL, degree, season.
Optional: requisition ID.

Maintainers merge accepted issues with `python scripts/merge_issue.py`, which
assigns a stable internship ID and sets `source: issue`. Duplicate IDs are skipped.

Do not open a listings-JSON pull request for a new req.

### 2. Scrapers and allowlist (pull requests)

PRs are welcome for:

- Company scrapers under `config/scrapers/`
- Allowlist URL / ATS note fixes in `config/allowlist.json`
- Parking a future employer in `config/candidates.json`
- Docs, tests, and tooling

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and
[docs/SCRAPER_CHECKLIST.md](docs/SCRAPER_CHECKLIST.md).

### 3. Adding a company

v1 coverage was the locked twelve employers. Post-v1 waves add device companies
from `config/candidates.json` onto `config/allowlist.json` after an explicit
scope decision. Wave 2 promoted the remaining parked device companies; new
employers still start in `candidates.json`. Hospitals and pharma stay out.

1. **Candidates** — open a PR (or issue) that adds the employer to
   `config/candidates.json` with a public intern/university hub URL. Do not add
   it to the allowlist in the same change.
2. **Allowlist** — maintainers promote a candidate into `config/allowlist.json`
   only after an explicit scope decision.
3. **Scraper** — once the company is allowlisted, add
   `config/scrapers/<company>_scraper.py` (Greenhouse / Lever / stable JSON
   preferred). Workday-only employers may stay on a program-fallback row.

### 4. Docs and tooling

Improvements to contributing docs, schema notes, tests, and automation are
welcome as pull requests.

## Maintainer merge path (issue → catalog)

Community members stop at the issue. Maintainers then:

1. Confirm the company is on the allowlist (not only `candidates.json`).
2. Confirm the apply URL is a real req or program page, not a raw Workday search.
3. Merge with identity + schema:

   ```bash
   python scripts/merge_issue.py \
     --company "Medtronic" \
     --title "Software Engineer Intern" \
     --location "Minneapolis, MN" \
     --apply-url "https://example.com/job/R-12345" \
     --degree Unspecified \
     --season summer-2027 \
     --req-id R-12345
   ```

   Use `--dry-run` to print the row without writing. The script sets
   `source: issue`, computes the UUID v5 internship ID, refuses companies off
   the allowlist, and skips IDs already in active or archived catalogs.
4. `python scripts/validate_data.py`
5. `python scripts/generate_dashboard.py` so the README picks up the row.
6. Open a maintainer PR (do not push listings straight to `main`).

Force-close a listing via `python scripts/archive_closed.py --force-close <id>`
(see [docs/AUTOMATION.md](docs/AUTOMATION.md)).

## What we do not accept

- Pull requests that hand-edit `data/active/internships.json` or
  `data/archived/internships.json`
- Raw scrape dumps or unprocessed ATS exports
- Adding candidate employers to the allowlist without a scope change
- Secrets, cookies, API keys, or `.env` files

## Reporting security issues

See [SECURITY.md](SECURITY.md). Do not file a public issue for vulnerabilities.

## Questions

Open a blank issue for catalog corrections (broken Apply links, wrong location)
if they do not fit the Add internship form.
