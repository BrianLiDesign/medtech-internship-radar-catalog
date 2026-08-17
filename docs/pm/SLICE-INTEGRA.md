# Slice — Integra LifeSciences Kentico job search

**Status:** Implemented with mocked tests. Live intern-keyword search on 2026-08-16 returned 0 results (171 unfiltered reqs, none titled intern/co-op/student). Production catalog is unchanged until daily refresh.

**Locked constraints:** Public Kentico HTML partials at `GET /api/jobs/search?keyword=intern` only. Do not reverse-engineer Workday CXS/search. Individual Workday **job** apply URLs with JR- ids are allowed as `apply_url`. Treat listing HTML as untrusted (title/location/href only). Mock HTTP in CI. Do not use `jobs.integralife.com` (redirects to the marketing careers hub) or `/api/content/jobs` (404).

## Scope

| Company | Source |
|---------|--------|
| Integra LifeSciences | `https://www.integralife.com/api/jobs/search?pageUrl=/careers/job-search&keyword=intern` |

Adapter: `config/scrapers/integra_life_sciences_scraper.py` via `scripts/kentico_jobs_adapter.py`.

## Behaviors to test

1. Framework registers `Integra LifeSciences`.
2. Fixture US STEM intern is a `posting`; HR, sales, and non-US intern titles drop.
3. Empty intern-keyword partial keeps the program-fallback hub.
4. 403 soft-fail.
