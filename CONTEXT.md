# Context

Domain glossary for the MedTech Internship Radar Catalog. Use these terms in code, docs, issues, and architecture discussions.

## Catalog

The published dataset in `data/active/internships.json` and `data/archived/internships.json`.
The catalog is the **source of truth**. A future website may consume it; it must not become the source of truth.

## Internship row

One JSON object conforming to `data/schema.json`. Either a **posting** (specific req + apply URL) or a **program fallback** (company internship portal when individual reqs are not scrapeable).

## Internship ID

A stable UUID v5 from `scripts/internship_ids.py`. Layered key: `company|req_id`, else canonical apply URL, else `company|title|location`. Program fallback: `company|program_url`. IDs must not change when a row is updated. Use this repo’s namespace — never the student-program catalog namespace.

## Season

A field on each row (`summer-2027`, later `summer-2028`, …). The repo is **evergreen**. The README’s leading table is chosen by `config/current_season.json`, a maintainer flag — not a calendar cutover and not a new repository.

## Allowlist

`config/allowlist.json` — companies approved for automated scraping and README coverage. v1 is twelve device + diabetes employers. Post-v1 wave 1 adds J&J MedTech, Siemens Healthineers, Philips, Penumbra, and Align. Wave 2 adds Smith+Nephew through Inspire Medical (32 total).

## Candidates

`config/candidates.json` — device companies parked for a later allowlist wave. Wave 2 emptied the parked list. Hospitals/pharma stay out.

## Role family

README grouping and schema enum: Software; BME/R&D; Electrical/firmware; Mechanical/robotics; Data/ML; Quality/manufacturing; Other STEM.

## STEM intern

At an allowlisted company: engineer, scientist, analyst, and similar (including quality, manufacturing, and regulatory STEM). Not business, sales, or HR.

## Summer co-op

A co-op whose term is Summer 2027 / summer-shaped. In v1. Multi-term rotating co-ops and fall/spring-only are out.

## Age

README recency for **postings**: `posted_at` if known, else `first_seen`. Program-fallback hubs have no posting date, so Age is `—` unless `posted_at` is set. Not `last_seen` / last-verified.

## Verification / liveness

`last_seen` and `miss_count`. Archive after ATS-closed **or** two consecutive daily misses. Program-fallback rows need a higher bar than a single failed fetch.

## Refresh

The daily automation that re-scrapes allowlisted companies, archives closed rows, regenerates the README, and opens a PR — never pushes listings directly to `main`.

## Contribution phases

1. **Maintainer-managed** (v1): automation + maintainers edit catalog JSON; community files structured issues and scraper/allowlist PRs.
2. Issue-based suggestions (already in v1 as backfill).
3. Validated PRs for listings: not v1.

## License split

- **Data** (`data/`): CC-BY 4.0
- **Code** (everything else): MIT

## Brand

Public docs and README do **not** mention Student Program Radar. This is a standalone intern listings catalog. Internally, that other repo is only a **pattern** for skeleton habits (schema gate, allowlist, generated README, refresh-via-PR).
