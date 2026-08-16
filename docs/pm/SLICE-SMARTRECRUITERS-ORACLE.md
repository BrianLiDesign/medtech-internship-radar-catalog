# Slice — SmartRecruiters + Oracle CE adapters

**Status:** Implemented with mocked tests. Live boards on 2026-08-15 had no kept US STEM intern reqs (Intuitive intern title is Fall; Cooper/Hologic intern-keyword hits were Costa Rica or non-intern titles).

**Locked constraints:** Public JSON only. Do not reverse-engineer Workday CXS/search. Mock HTTP in CI. Do not write fixtures into production catalog.

## Scope

| Company | Endpoint |
|---------|----------|
| Intuitive | `GET https://api.smartrecruiters.com/v1/companies/Intuitive/postings` |
| CooperCompanies | `GET https://hcjy.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions` (`finder=findReqs;siteNumber=CX_1`) |
| Hologic | `GET https://ebwb.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions` (`siteNumber=CX`) |

Shared adapters: `scripts/smartrecruiters_adapter.py`, `scripts/oracle_ce_adapter.py`.

## Live check (2026-08-15)

- Intuitive: 645 SmartRecruiters postings; intern-shaped title is Fall 2026 (inclusion drops). `International` in FT titles is not intern.
- Cooper/Hologic: Oracle CE intern keyword returns many reqs; intern-titled rows on the first pages were Costa Rica. US STEM intern reqs will be picked up when they open.

## Behaviors to test

1. Framework registers `Intuitive`, `CooperCompanies`, `Hologic` (not the shared base classes).
2. Fixture US STEM intern is a `posting`; HR, non-US, sales, and fall drop.
3. Empty payload keeps the program-fallback hub.
4. 403 / unexpected payload soft-fail.
