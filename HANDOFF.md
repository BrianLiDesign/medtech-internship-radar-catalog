# Handoff: MedTech Internship Radar Catalog (v1)

**Status:** Ready for implementation — do not reopen grill decisions unless scope changes  
**Audience:** Engineer (or PM + engineer) building the repo from zero  
**Source:** Design grill (2026-08-14) in `student-program-radar-catalog` chat  
**Repo:** `medtech-internship-radar-catalog`  
**Pattern source (ideas only):** `../student-program-radar-catalog` — copy skeleton habits, **not** program scrapers or the program schema

**Build order:** [PLAN.md](PLAN.md) — start at Slice 1; do not open scrapers until Slice 2’s README exists.  
**PM kickoff prompt:** [HANDOFF_PM.md](HANDOFF_PM.md)

Next session skills: **tdd** for schema/IDs/generator; **diagnose** for scraper/ATS failures; **context7-mcp** for `requests`, `beautifulsoup4`, `jsonschema`. Do **not** use live network in CI.

---

## 1. Goal

Ship a **public, evergreen listings catalog** of **US Summer 2027 STEM internships** (plus summer-shaped co-ops) at **12 flagship device + diabetes companies**, as JSON + a Simplify-style generated README. Students browse by role family and click **Apply**.

### Success looks like

1. GitHub README is discover-first: jump links by role family → tables with Apply badges → compact stats/health → Quick Start/docs.
2. All **12 companies** appear. Posting-level rows where the ATS allows; otherwise one **program-fallback** row with a real apply/careers URL.
3. Daily automation checks liveness and archives closed rows after **ATS-closed or two consecutive daily misses**.
4. Community adds reqs via **structured issues**; scrapers/allowlist via **PRs**; nobody hand-edits listings JSON.
5. `season` is a field. README default season is a maintainer flag (`summer-2027` for v1). Next cycle does **not** fork this repo.

### Explicit non-goals (v1)

- Website / GitHub Pages / alerts / Slack / Discord
- Big Tech health orgs, digital-health startups, hospitals, pharma, J&J MedTech, Siemens, Philips
- New-grad full-time, PhD-only, fall/spring-only or multi-term rotating co-ops
- Visa/sponsorship as a README column or v1 filter
- Cross-links or combined tables with Student Program Radar (separate brand)
- Yearly cycle repos (`…-2027` / `…-2028`)
- Shared Python package extracted from the program catalog
- Perfect Workday reverse-engineering for all 12 companies
- Hand-edited `data/active/internships.json`

---

## 2. Locked product decisions

Do not reopen unless the owner explicitly changes scope.

| # | Decision | Choice |
|---|----------|--------|
| Q1 | Audience | Public catalog (not a personal tracker) |
| Q2 | Home | New sibling repo |
| Q3 | Inclusion | Company-first, then STEM roles at those companies |
| Q4 | v1 companies | 12 flagship device + diabetes (list below) |
| Q5 | Role breadth | All STEM (engineer / scientist / analyst incl. quality, manufacturing, regulatory STEM). Business / sales / HR out |
| Q6 | Unit of listing | Job posting; **program-row fallback** if that is all the company has |
| Q7 | v1 content window | Summer 2027 intern + summer co-op |
| Q7b | Cycle architecture | **Evergreen repo**, `season` on each row; not a new repo per year |
| Q8 | Student surface | JSON + generated README now; website later as a **consumer** |
| Q9 | Geography | US postings only (including US-remote) |
| Q10 | Ingest | Hybrid: scrape stable ATS; seed Workday from program pages + known reqs; issues backfill |
| Q11 | README grouping | Role family; company is a column |
| Q12 | Degree | Bachelor’s and master’s internships. PhD-only and new-grad out |
| Q13 | Closed rows | Move to `data/archived/` (+ inactive README section or `README-Inactive.md`) |
| Q14 | Columns | Company \| Role \| Location \| Degree \| Apply \| Age |
| Q15 | Allowlist | The 12 names below; J&J / Siemens / Philips / Penumbra / Align → `candidates.json` |
| Q16 | Code strategy | **Pattern copy, new code.** Same skeleton; internship-native schema and ATS adapters |
| Q18 | Repo name | `medtech-internship-radar-catalog` (later app may use `medtech-internship-radar`) |
| Q19 | Age | Prefer `posted_at`; else `first_seen`. Not last-verified |
| Q20 | Season default | Maintainer file `config/current_season.json` |
| Q21 | Identity | UUID v5: `req_id` → canonical apply URL → `company\|title\|location`. Program fallback: `company\|program_url` |
| Q22 | v1 publish bar | All 12 named; posting rows where possible; fallback + seed/issue otherwise; no company with zero rows |
| Q23 | Co-op | Summer 2027 STEM co-ops in; multi-term / off-season out |
| Q24 | Close rule | ATS closed **or** two consecutive daily misses; issues can force-close; program-fallback does not die on one miss |
| Q25 | Contribution | Structured issues for reqs; PRs for scrapers/allowlist; maintainers/automation own JSON |
| Q26 | Work auth | Store `work_auth` in JSON when stated; do not filter v1 README |
| Q27 | Returning/internal | Keep; tag `eligibility` in JSON; no extra README column |
| Q28 | License | CC-BY 4.0 data (`data/`); MIT code (everything else) |
| Q29 | Brand | Fully separate from Student Program Radar — **no mention** in this README |
| Q30 | Apply control | In-repo `assets/apply.svg`; no `apply_url` → no row |
| Q31 | Multi-city | Explode only when apply URLs differ; else join cities (truncate `+N` if huge) |
| Q32 | Unknown degree | JSON `unspecified`; README shows `BS/MS` |
| Q33 | v1 cut | Listings only |

### v1 allowlist (fixed)

1. Medtronic  
2. Intuitive  
3. Abbott  
4. Dexcom  
5. Insulet  
6. Tandem  
7. Stryker  
8. Boston Scientific  
9. Edwards  
10. BD  
11. Zimmer Biomet  
12. GE HealthCare  

**Candidates (not v1 scrapers):** J&J MedTech, Siemens Healthineers, Philips, Penumbra, Align.

### Role families (README sections + schema enum)

- Software  
- BME/R&D  
- Electrical/firmware  
- Mechanical/robotics  
- Data/ML  
- Quality/manufacturing  
- Other STEM  

Omit empty sections. Jump links at top with counts.

---

## 3. Current baseline (start state)

| Fact | Value |
|------|--------|
| This repo | Empty git repo + this handoff (no scrapers, no schema yet) |
| Pattern repo | `C:\Users\brian\Documents\GitHub\student-program-radar-catalog` |
| What to copy as *ideas* | `data/schema.json` + `scripts/validate_data.py` + `scripts/program_ids.py` + `scripts/generate_dashboard.py` + `config/allowlist.json` + `config/candidates.json` + daily refresh-via-PR + dual license + issue templates + “no hand-edit catalog JSON” |
| What **not** to copy | `config/scrapers/*` program scrapers, program `role_type` enums, 60-day program SLO, ambassador README copy, any cross-link to that product |
| ID namespace | **New** UUID v5 namespace — do **not** reuse the program catalog namespace |

Expect **most of the 12 to be Workday**. v1 must still name all 12 via program-fallback and/or seeds. Do not block publish on a perfect Workday adapter.

---

## 4. Target skeleton (pattern copy)

```text
medtech-internship-radar-catalog/
├── AGENTS.md
├── CONTEXT.md
├── README.md                 # generated; do not hand-edit tables
├── README-Inactive.md        # optional; archived rows for the current season
├── LICENSE.md                # MIT (code)
├── LICENSE-DATA.md           # CC-BY 4.0 (data/)
├── NOTICE
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Makefile                  # lint test validate e2e (same command names as pattern repo)
├── assets/apply.svg
├── config/
│   ├── allowlist.json
│   ├── candidates.json
│   └── current_season.json   # { "season": "summer-2027" }
├── data/
│   ├── schema.json
│   ├── active/internships.json
│   └── archived/internships.json
├── docs/
│   ├── SCHEMA.md
│   ├── AUTOMATION.md
│   ├── DEVELOPMENT.md
│   └── adr/
├── scripts/
│   ├── internship_ids.py     # UUID v5 identity (layered keys)
│   ├── validate_data.py
│   ├── generate_dashboard.py
│   ├── scrape_internships.py
│   ├── archive_closed.py     # two-miss / ATS-closed / force-close
│   └── scraper_framework.py  # internship-native base; do not import program scrapers
├── config/scrapers/          # one module per company, registered by *Scraper name
└── .github/
    ├── workflows/            # CI + daily refresh PR (never push listings to main)
    ├── ISSUE_TEMPLATE/       # add-internship.yml
    └── pull_request_template.md
```

Python **3.9+**. Ruff. Pytest with **mocked HTTP only** in CI.

---

## 5. Record shape (implement in `data/schema.json`)

Internship-native. Required fields should make a README row possible.

**Required (v1):** `id`, `company`, `title`, `apply_url`, `season`, `role_family`, `location`, `degree`, `row_kind`, `source`, `first_seen`, `last_seen`

**Important optional:** `req_id`, `posted_at`, `work_auth`, `eligibility` (`open` \| `returning`), `closed_at`, `close_reason`, `miss_count`, `canonical_apply_url`, `program_url`, `ats`, `short_description`

| Field | Notes |
|-------|--------|
| `id` | UUID v5 from layered identity (Q21). New namespace UUID, documented in ADR |
| `row_kind` | `posting` \| `program_fallback` |
| `season` | `summer-2027` for v1 (`config/current_season.json` is the README default, not a filter that deletes other seasons from JSON) |
| `role_family` | Enum in §2 |
| `degree` | `bs` \| `ms` \| `bs_ms` \| `unspecified` — README: unspecified → `BS/MS` |
| `location` | US city/state list or `Remote (US)`; join with `; ` when one apply URL, many sites |
| `source` | `scrape` \| `seed` \| `issue` |
| `work_auth` | `citizen_only` \| `us_auth_no_sponsor` \| `unspecified` (and similar; keep enum small) |
| `posted_at` / `first_seen` | Age uses posted if present else first_seen |
| `last_seen` | Liveness; **not** Age |
| `miss_count` | Consecutive daily misses; archive at 2 unless ATS already closed |

**Identity function (must be deterministic and tested):**

1. If `req_id` present → `company|req_id`  
2. Else if apply URL present → `company|canonical_url` (strip tracking/query junk; never raw Workday search URLs)  
3. Else `company|normalized_title|normalized_location`  
4. Program fallback: `company|program_url`  
5. UUID v5 of that key in **this repo’s** namespace  

**Inclusion filters (shared, unit-tested):**

- Company in allowlist  
- US (or US-remote)  
- STEM (not business/sales/HR)  
- Intern **or** summer-2027 co-op  
- Open to BS and/or MS (drop PhD-only and new-grad FT)  
- `apply_url` required  

---

## 6. Workstreams & sequencing

```text
Epic 0  Repo bootstrap (license, CI, AGENTS, season flag)
   │
Epic 1  Schema + IDs + empty catalog + validate
   │
Epic 2  README generator + Apply badge (can use fixture JSON)
   │
Epic 3  Allowlist + ATS research + program-fallback seeds for all 12
   │
Epic 4  Ingest pipeline (scrape adapters where easy; seeds; issue merge)
   │
Epic 5  Close/archive + daily refresh-via-PR
   │
Epic 6  Contribution templates + docs + v1 publish bar
```

**Rule:** Do not wait for Workday adapters to generate the README. Fixture + seeds should produce a 12-company table first. Then thicken posting rows.

Suggested lanes if split:

| Lane | Focus |
|------|--------|
| **A — Catalog core** | Schema, IDs, validate, generator, Apply asset |
| **B — Coverage** | Allowlist, ATS notes, fallback URLs, Greenhouse/Lever adapters, seeds |
| **C — Pipeline** | Liveness, archive, daily workflow, issue intake |

---

## 7. Epics → tickets

### Epic 0 — Repo bootstrap

#### T0.1 License, git hygiene, Python project
- **Work:** MIT `LICENSE.md`; CC-BY `LICENSE-DATA.md` (or `data/LICENSE`); `NOTICE`; `.gitignore`; `pyproject.toml` / requirements; Makefile targets `lint`, `format`, `test`, `validate`, `e2e` (e2e can be a stub until Epic 1–2 exist).
- **AC:**
  - [ ] Dual license documented in README footer
  - [ ] `python -m compileall` / ruff runnable
  - [ ] No secrets committed

#### T0.2 Agent + domain docs
- **Work:** Keep `AGENTS.md` / `CONTEXT.md` aligned with this handoff (already seeded). Add `docs/adr/0001-dual-license.md`, `0002-internship-ids-uuid-v5.md`, `0003-maintainer-managed-catalog.md`.
- **AC:**
  - [ ] ADRs match locked decisions (new ID namespace; no hand-edit JSON)
  - [ ] AGENTS.md forbids copying program scrapers and forbids mentioning Student Program Radar in the public README

#### T0.3 `config/current_season.json`
- **Work:** `{ "season": "summer-2027" }`
- **AC:**
  - [ ] Generator reads this for which season’s **active** table to lead with
  - [ ] Changing the file does not require a code change

---

### Epic 1 — Schema, IDs, validation

#### T1.1 `data/schema.json` + `docs/SCHEMA.md`
- **Depends on:** T0.1  
- **AC:**
  - [ ] Required fields from §5
  - [ ] Enums for `role_family`, `row_kind`, `season` (at least `summer-2027`; allow future seasons), `degree`, `source`
  - [ ] Example fixture with one `posting` and one `program_fallback`

#### T1.2 `scripts/internship_ids.py` (TDD)
- **Depends on:** T1.1  
- **AC:**
  - [ ] Layered key tests: req_id wins; URL canonicalization strips `utm_*` / session-looking params; program_url path
  - [ ] Same inputs → same UUID; different companies → different IDs
  - [ ] Namespace UUID is unique to this catalog (documented)

#### T1.3 `scripts/validate_data.py`
- **Depends on:** T1.1  
- **AC:**
  - [ ] Validates active + archived JSON
  - [ ] Fails CI on schema miss, duplicate `id`, missing `apply_url`
  - [ ] Empty `[]` catalogs are valid so bootstrap can land

---

### Epic 2 — README dashboard (Track 1 — start as soon as fixtures exist)

#### T2.1 `assets/apply.svg`
- **AC:** Compact, readable ~80–100px wide on GitHub; stored in this repo only (no hotlinks)

#### T2.2 `scripts/generate_dashboard.py`
- **Depends on:** T1.1, T2.1, T0.3  
- **Layout:**
  1. Title + one-line pitch (Summer 2027 MedTech STEM internships — **do not** mention the other radar)
  2. Role-family jump links with counts (current season, active only)
  3. Tables: Company \| Role \| Location \| Degree \| Apply \| Age  
  4. Compact stats + automation health placeholders  
  5. Quick Start / docs / license  
- **Rules:** Current season from config; `degree` unspecified → `BS/MS`; Age from `posted_at` else `first_seen` as `3d` / `1mo`; no row without `apply_url`; empty families omitted; archived not in main tables (link Inactive if present).
- **AC:**
  - [ ] Generator is the only writer of README tables
  - [ ] Fixture with 12 fallback rows renders 12 companies
  - [ ] Tests for sort, Age fallback, degree display, Apply markdown

#### T2.3 Inactive archive view
- **Depends on:** T2.2  
- **Work:** `README-Inactive.md` **or** a README section below the fold for archived current-season rows (Simplify-style). Prefer a separate file if the main table would get long.
- **AC:**
  - [ ] Closed rows leave the main table the day they archive
  - [ ] Archive retains `closed_at` / `close_reason`

---

### Epic 3 — Coverage for all 12 (publish bar)

#### T3.1 Allowlist + candidates JSON
- **Work:** `config/allowlist.json` with official careers / university / internship hub URLs (research live; do not invent). `config/candidates.json` for J&J, Siemens, Philips, Penumbra, Align.
- **AC:**
  - [ ] All 12 v1 names present with at least one public hub URL
  - [ ] Notes field for suspected ATS (`workday` / `greenhouse` / `lever` / `unknown`) — verified, not guessed in final notes

#### T3.2 Program-fallback seeds
- **Depends on:** T1.2, T3.1  
- **Work:** One `program_fallback` row per company (`source: seed`) so the README can ship before adapters. `apply_url` = internship program or university recruiting page.
- **AC:**
  - [ ] 12 schema-valid rows; all pass validate
  - [ ] Generator shows all 12
  - [ ] Seeds live in a maintainer-owned seed file **or** first scrape output — **not** a hand-maintained README

#### T3.3 Inclusion classifier (TDD)
- **Work:** Shared functions: STEM vs business; intern vs summer co-op vs off-season vs new-grad vs PhD-only; US location parse.
- **AC:**
  - [ ] Unit tests with real-ish title strings (“Regulatory Affairs Intern” in; “HR Intern” out; “Summer Co-op Software” in; “Fall Co-op” out)

---

### Epic 4 — Hybrid ingest

#### T4.1 Scraper framework (internship-native)
- **Work:** Base class: fetch with timeouts/rate limits; `find_posting_urls()` / `parse_posting()`; map into schema; attach `source: scrape`. **Do not** import `config/scrapers` from the program catalog.
- **AC:**
  - [ ] Registration by `CompanyScraper` naming
  - [ ] Mocked HTTP tests
  - [ ] Soft-fail artifact when blocked (no invented postings)

#### T4.2 Adapters for scrapeable ATS first
- **Depends on:** T4.1, T3.3  
- **Work:** Implement Greenhouse/Lever/JSON endpoints **only for companies that actually use them** (confirm in T3.1). Workday companies stay on fallback + seeds + issues until a dedicated adapter is justified.
- **AC:**
  - [ ] Posting rows upsert by ID; `first_seen` stable; `last_seen` updates
  - [ ] STEM/US/season filters applied
  - [ ] Multi-city: explode only if apply URLs differ

#### T4.3 Issue → catalog path
- **Depends on:** T1.2  
- **Work:** Issue template: company (dropdown of 12), title, location, apply URL, degree, season, optional req_id. Maintainer script or documented manual merge that runs identity + schema (still no raw JSON PRs from community).
- **AC:**
  - [x] Template exists
  - [x] Merge path sets `source: issue` and does not duplicate IDs
  - [x] CONTRIBUTING.md says listings JSON is automation/maintainer only

#### T4.4 Returning / work_auth parse (best-effort)
- **Depends on:** T4.2  
- **Work:** If text says returning/internal → `eligibility: returning`. If citizen-only or no sponsorship → `work_auth`. Never drop the row for v1.
- **AC:**
  - [ ] Tests for a few keyword cases; default `eligibility: open`, `work_auth: unspecified`

---

### Epic 5 — Close detection + daily refresh

#### T5.1 Archive rules
- **Depends on:** T4.1  
- **Work:** `miss_count`; archive when ATS status closed **or** `miss_count >= 2`. Force-close via issue label/script. Program-fallback: do not archive on a single miss; require maintainer/issue or program URL gone (404/410 twice).
- **AC:**
  - [ ] Tests for grace period, force-close, fallback exception
  - [ ] Archived JSON + generator drop from main table

#### T5.2 Daily workflow
- **Work:** GitHub Action: scrape → validate → archive → generate README → **open PR** on `automation/daily-catalog-refresh` (or equivalent). Never push listings straight to `main`. Health metadata for README (last sweep, updated, failed scrapers, archived count).
- **AC:**
  - [ ] Documented in `AUTOMATION.md`
  - [ ] Matches “refresh via PR” habit from the pattern repo
  - [ ] CI on that PR runs validate + tests (mocked)

---

### Epic 6 — Docs, QA, publish bar

#### T6.1 Public docs
- **Work:** CONTRIBUTING.md, SECURITY.md (private advisories), DEVELOPMENT.md, SCRAPER_CHECKLIST.md (internship version). README pitch must **not** mention Student Program Radar.
- **AC:**
  - [x] Contribution phases match Q25
  - [x] How to add a company (candidates → allowlist → scraper) is documented

#### T6.2 PM/owner acceptance
- **Depends on:** T2.2, T3.2, T5.2 (or waivers)  
- **Checklist:**
  - [x] All 12 companies have ≥1 row with working Apply URL
  - [x] Role-family jump links work
  - [x] Age and Degree columns follow locked display rules
  - [x] At least one posting-level row exists **or** waiver: “all 12 still Workday fallback”
  - [x] Daily PR path dry-run once
  - [x] No hand-edited README tables
  - [x] No brand cross-links

PM sign-off 2026-08-14. Waivers: no GitHub remote yet — T5.2 is the documented local fixture dry-run (`python scripts/refresh_catalog.py --fixture tests/fixtures/boston_scientific_pcsx.json`) plus workflow YAML; live Actions after `origin` exists. URL quality flags (not blockers): Dexcom Phenom intern listing; Zimmer Biomet Grow With Us mixes internships with leadership programs. Eleven companies remain program-fallback (Workday/unknown); Boston Scientific has posting rows. 20 extra device employers stay in `config/candidates.json` (not v1 allowlist).

---

## 8. Implementation notes (avoid known traps)

1. **Workday 200 ≠ open.** Login/search HTML is not a live req. Prefer ATS status; otherwise miss counting.  
2. **Do not use raw Workday search URLs as identity.** They rot and duplicate.  
3. **60-day program SLO is wrong here.** Intern rows die in days.  
4. **Do not default-filter no-sponsorship.** It would empty the list.  
5. **Separate brand:** zero README/docs references to student-program-radar in *public* files. Internal AGENTS.md may cite it as a *pattern* repo only.  
6. **Website later** consumes `data/active/internships.json`; keep the schema boring and versioned.  
7. **Season overlap:** when `summer-2028` rows appear, do not auto-flip the README; only `current_season.json` changes leadership. Overlap UI (two sections) is post-v1.

---

## 9. Out of scope reminders for the next agent

- Do not implement `medtech-internship-radar` (the website).  
- Do not add J&J/Siemens as v1 allowlist entries.  
- Do not open a `medtech-internships-2028` repo.  
- Do not commit live scrape dumps that include PII.  
- Do not treat this handoff as permission to edit `student-program-radar-catalog` listings JSON.

---

## 10. Suggested first commits (order)

1. Epic 0 bootstrap + licenses  
2. Schema + ID + validate + empty `internships.json`  
3. Apply SVG + generator + 12 seed fallback fixtures  
4. Allowlist research + classifier tests  
5. Framework + first real adapter (whichever company is actually Greenhouse/Lever)  
6. Archive + daily PR workflow  
7. Issue template + CONTRIBUTING  

When implementation starts, tick AC in this file or break tickets into GitHub issues (`to-issues` skill) without changing locked decisions.
