# Slice — J&J internships landing adapter

**Status:** Implemented with mocked tests. Live intern cards on 2026-08-15 were non-US (Suzhou, Shanghai, Aachen, LATAM). Production catalog is unchanged until daily refresh.

**Locked constraints:** Public internships landing HTML only (`/en/early-career-programs/internships/`). Do not crawl the unfiltered `/en/jobs/` board (search params are ignored). Do not reverse-engineer Workday CXS/search. Treat listing HTML as untrusted (title/location/href only). Mock HTTP in CI.

## Scope

| Company | Source |
|---------|--------|
| J&J MedTech | `https://www.careers.jnj.com/en/early-career-programs/internships/` |

Adapter: `config/scrapers/jj_med_tech_scraper.py`.

## Behaviors to test

1. Framework registers `J&J MedTech`.
2. Fixture US STEM intern is a `posting`; HR, sales, and non-US intern titles drop.
3. Empty landing HTML keeps the program-fallback hub.
4. 403 soft-fail.
