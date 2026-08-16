# Slice — Phenom `/widgets` adapters (seven career sites)

**Status:** Implemented with mocked tests. Live intern-keyword hits on 2026-08-15 were mostly non-US, sales, or fall co-ops, except Siemens Healthineers (US intern titles present). Hubs stay in the production catalog until daily refresh.

**Locked constraints:** Public Phenom JSON only. Do not reverse-engineer Workday CXS/search. Individual Workday **job** apply URLs with req ids are allowed as `apply_url`. Mock HTTP in CI.

## Problem

Several allowlisted companies sit on Phenom career sites in front of Workday apply. Those sites expose `POST {origin}/widgets` (`ddoKey=refineSearch`) — not a Workday search API.

## Scope

| Company | Origin | Don’t |
|---------|--------|-------|
| Abbott | `https://www.jobs.abbott` | Workday CXS / search URLs as identity |
| Zimmer Biomet | `https://careers.zimmerbiomet.com` | Expand allowlist |
| GE HealthCare | `https://careers.gehealthcare.com` | Write fixture JSON into production catalog |
| STERIS | `https://careers.steris.com` | Register the shared `PhenomInternshipScraper` base as a company |
| CONMED | `https://careers.conmed.com` | |
| Philips | `https://www.careers.philips.com` | |
| Siemens Healthineers | `https://careers.siemens-healthineers.com` | |

Shared adapter: `scripts/phenom_adapter.py`. Thin company files stay `config/scrapers/<company>_scraper.py`.

## Live check (2026-08-15)

- `/widgets` JSON 200: Abbott, Zimmer Biomet, GE HealthCare, STERIS, CONMED, Philips, Siemens Healthineers.
- Not this slice: Dexcom 401; Stryker/BD/Baxter/Hologic/Align/Intuitive 404; Integra/Olympus/Teleflex HTML. Edwards `/widgets` is a widget shell, not `refineSearch`. Eightfold PCSX guesses for remaining companies: no hits.

## Behaviors to test

1. Framework registers the seven company names (not `Phenom Internship`).
2. Fixture US STEM intern is a `posting`; HR, non-US, sales, and fall co-op titles drop.
3. Empty `jobs` list yields `postings == []` (upsert keeps the hub).
4. 403 / unexpected payload soft-fail with a failure artifact.
5. Discovery uses POST `/widgets`, not GET.

## Done when

Lint + pytest + validate green. `--fixture` remains Boston Scientific-only.
