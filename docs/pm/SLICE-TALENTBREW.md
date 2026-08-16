# Slice — TalentBrew search-jobs adapters (BD, Baxter)

**Status:** Implemented with mocked tests. Live intern-keyword search on 2026-08-15 includes a US Engineering Intern at BD (Canaan, CT). Baxter intern-keyword hits were mostly non-US or non-intern titles. Production catalog is unchanged until daily refresh.

**Locked constraints:** Public TalentBrew `GET /en/search-jobs/results` JSON only (listing HTML inside `results`). Do not reverse-engineer Workday CXS/search. Treat listing HTML as untrusted (title/location/href only). Mock HTTP in CI.

## Scope

| Company | Origin |
|---------|--------|
| BD | `https://jobs.bd.com/en/search-jobs/results` |
| Baxter | `https://jobs.baxter.com/en/search-jobs/results` |

Shared adapter: `scripts/talentbrew_adapter.py`.

## Behaviors to test

1. Framework registers `BD` and `Baxter` (not the shared base class).
2. Fixture US STEM intern is a `posting`; HR, sales, and non-US intern titles drop.
3. Empty `results` keeps the program-fallback hub.
4. 403 / unexpected payload soft-fail.
