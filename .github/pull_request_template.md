## Summary

- What changed and why?

## Type

- [ ] Scraper / allowlist / candidates
- [ ] Docs or tooling
- [ ] Automation refresh (maintainers / daily workflow only)

## Verification

- [ ] `python -m pytest -q`
- [ ] `python scripts/validate_data.py`
- [ ] HTTP is mocked in tests (no live ATS calls in CI)
- [ ] No secrets, cookies, API keys, or `.env` files

## Catalog JSON

Community PRs must **not** edit `data/active/internships.json` or `data/archived/internships.json`.
Those files are automation- and maintainer-owned. Suggest new reqs with the
**Add internship** issue template instead.

If this is the daily refresh PR, listings + generated README changes are expected.

## Scrapers

If you added or changed a scraper, follow [docs/SCRAPER_CHECKLIST.md](docs/SCRAPER_CHECKLIST.md).
