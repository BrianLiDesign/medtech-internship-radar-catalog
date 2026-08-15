# Slice — Penumbra Lever + Inspire Greenhouse adapters

**Status:** Implemented and review-fixed (mocked tests green). Live boards had no US STEM intern reqs on 2026-08-15, so hubs stay until those postings open.

Review follow-up: Penumbra now maps Lever `country=US` + `Remote` / city-without-state into locations inclusion can keep.  
**Locked constraints:** No Workday reverse-engineering. Mock HTTP in CI. Do not invent rows.

## Problem

The catalog can list individual reqs (`row_kind: posting`) only where a public JSON ATS adapter exists. Today that is Boston Scientific Eightfold. Penumbra (Lever) and Inspire Medical (Greenhouse) are confirmed JSON boards still sitting on program-fallback hubs.

## Scope

| Do | Don’t |
|----|--------|
| `PenumbraScraper` → `GET https://api.lever.co/v0/postings/penumbrainc?mode=json` | Workday / Phenom / SuccessFactors / Oracle |
| `InspireMedicalScraper` → `GET https://boards-api.greenhouse.io/v1/boards/inspiremedicalsystemsinc/jobs` | `content=true` (descriptions not needed to include) |
| Filter through `include_posting(title, location)` | Drop hubs when the adapter returns zero US STEM intern reqs |
| Mocked fixtures + registration tests | Write fixture JSON into `data/active/internships.json` |

## Live check (2026-08-15)

- Penumbra: 80 Lever postings; intern-shaped titles are Singapore and Warsaw only → inclusion drops them.
- Inspire: 37 Greenhouse jobs; **no intern titles** (all FT clinical/sales/corporate).

Adapters still ship so daily refresh picks up US STEM intern reqs when they open. Until then both companies stay on program-fallback.

## Behaviors to test

1. Framework registers `Penumbra` and `Inspire Medical`.
2. Fixture US STEM intern is a `posting`; HR intern, non-US intern, and full-time reqs are dropped.
3. Soft-fail (403) yields no rows and a failure artifact.
4. Empty / intern-less payload yields `postings == []` (upsert keeps the hub).
5. Lever `createdAt` milliseconds and Greenhouse `first_published` ISO become `posted_at`.

## Done when

`make lint test validate` green. `--fixture` remains Boston Scientific-only and still refuses the production catalog.
