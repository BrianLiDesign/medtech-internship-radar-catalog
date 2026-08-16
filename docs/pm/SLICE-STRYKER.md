# Slice — Stryker Paradox intern search

**Status:** Implemented with mocked tests. Live intern-keyword preload on 2026-08-15 listed non-US intern titles (Rome, Amsterdam, Warsaw, China, South Africa, Türkiye). US intern + employment-type filter was empty. Production catalog is unchanged until daily refresh.

**Locked constraints:** Public Paradox SSR `window.__PRELOAD_STATE__` on `GET /jobs?keyword=intern` only. Do not reverse-engineer Workday CXS/search. Individual Workday **job** apply URLs with req ids are allowed as `apply_url`. Mock HTTP in CI. HTML hydrates the first page of intern-keyword hits (10 of 30 on 2026-08-15); do not invent a private Paradox search API.

## Scope

| Company | Source |
|---------|--------|
| Stryker | `https://careers.stryker.com/jobs?keyword=intern` |

Adapter: `config/scrapers/stryker_scraper.py`.

## Behaviors to test

1. Framework registers `Stryker`.
2. Fixture US STEM intern is a `posting`; HR, sales, and non-US intern titles drop.
3. Empty `jobs` list keeps the program-fallback hub.
4. 403 soft-fail.
