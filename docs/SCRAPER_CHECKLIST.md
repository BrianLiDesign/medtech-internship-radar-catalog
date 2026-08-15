# Scraper authoring checklist

Use this checklist when adding or updating a company internship scraper.

v1 does **not** require a perfect Workday adapter. Prefer Greenhouse, Lever, or
other stable public JSON. If the ATS is Workday (or otherwise blocked), keep the
company on its program-fallback row and seed/issue backfill until an adapter is
justified.

## Before coding

- [ ] Company is on `config/allowlist.json` (candidates are not scrapers yet)
- [ ] Target pages are public and do not require authentication
- [ ] You have a stable listing or JSON endpoint — not a raw Workday search URL
- [ ] If the company is still a candidate, stop: promote via
      candidates → allowlist → scraper ([CONTRIBUTING.md](../CONTRIBUTING.md))

## Implementation

- [ ] Create `config/scrapers/<company>_scraper.py`
- [ ] Subclass `InternshipScraper` from `scripts/scraper_framework.py`
- [ ] Implement `find_posting_urls()` (discovery)
- [ ] Implement `parse_posting(url)` → schema-shaped dict, or `None` if invalid
- [ ] Class name follows `<Company>Scraper` for registry discovery
- [ ] Set `company` to the allowlist name exactly
- [ ] Do not hardcode internship IDs — `internship_ids.internship_id` assigns UUID v5
- [ ] Use framework `fetch` helpers (timeouts + rate limit); do not bypass them
- [ ] Soft-fail when blocked: write an artifact, emit **no invented rows**
- [ ] If the ATS has no individual reqs, emit one `program_fallback` row
- [ ] Filter through `scripts/inclusion.py` (STEM, intern/summer co-op, US)
- [ ] Multi-city: explode only when apply URLs differ

## Required fields (from `data/schema.json`)

`id`, `company`, `title`, `apply_url`, `season`, `role_family`, `location`,
`degree`, `row_kind`, `source`, `first_seen`, `last_seen`

Posting rows from scrapers use `row_kind: posting` and `source: scrape`.

## Testing

- [ ] Add tests with **mocked HTTP** (no live network in CI)
- [ ] Run `make lint test validate` before opening a PR (`make e2e` if refresh behavior changes)
- [ ] Output passes `python scripts/validate_data.py`
- [ ] Upsert keeps `first_seen` stable and updates `last_seen`

## Pull request

- [ ] PR does not hand-edit `data/active/internships.json` unless it is the
      automation refresh PR
- [ ] PR description notes which company and which public endpoint
- [ ] No secrets, cookies, or credentials in the diff

## Related docs

- [CONTRIBUTING.md](../CONTRIBUTING.md) — contribution phases
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [SCHEMA.md](SCHEMA.md)
- [AUTOMATION.md](AUTOMATION.md)
