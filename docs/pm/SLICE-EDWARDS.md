# Slice — Edwards Algolia InstantSearch

**Status:** Implemented with mocked tests. Live intern-keyword hits on 2026-08-16 were non-US (Singapore). US intern + country filter was empty. Production catalog is unchanged until daily refresh.

**Locked constraints:** Public Algolia InstantSearch `POST /1/indexes/*/queries` only (search-only frontend key). Do not reverse-engineer Workday CXS/search. Individual Workday **job** apply URLs with req ids are allowed as `apply_url`. Mock HTTP in CI. Do not treat Edwards `/api/jobs` HTML shells as a listing feed.

## Scope

| Company | Source |
|---------|--------|
| Edwards | `https://www.edwards.com/careers/jobsearch` InstantSearch index `EdwardsCareersJobs` |

Adapter: `config/scrapers/edwards_scraper.py` via `scripts/algolia_adapter.py`.

## Behaviors to test

1. Framework registers `Edwards`.
2. Fixture US STEM intern is a `posting`; HR, sales, and non-US intern titles drop.
3. Empty `hits` list keeps the program-fallback hub.
4. 403 soft-fail.
