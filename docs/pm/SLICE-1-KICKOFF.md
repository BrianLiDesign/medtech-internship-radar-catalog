# Slice 1 kickoff packet

**Role:** PM coordinates; engineer implements.  
**Backlog source:** [HANDOFF.md](../../HANDOFF.md) epics. This file maps those tickets onto Slice 1. Do not treat this as a second backlog.  
**Schedule:** [PLAN.md](../../PLAN.md) Slice 1.  
**Terms:** [CONTEXT.md](../../CONTEXT.md) — use posting, program fallback, season, Age, last_seen, allowlist, catalog.

**Status:** Drafted, waiting on owner “go” before an engineer session starts.

---

## Kickoff note

### Goal

Stand up a Python 3.9+ repo that can say **this catalog JSON is valid**. Empty `[]` catalogs must pass. Internship IDs are deterministic UUID v5 in **this repo’s** namespace.

Slice 1 is not student-facing yet. The first student-visible increment is Slice 2 (generated README with 12 program-fallback Apply links).

### Non-goals (do not start)

- README tables, Apply badge, generator (`generate_dashboard.py`)
- Scrapers, ATS adapters, Workday
- GitHub Actions / daily refresh PR
- Website, Pages, alerts, Slack
- Extra companies (J&J, Siemens, Philips, Penumbra, Align stay in candidates later)
- Visa/sponsorship as a README column or filter
- New season repos (`…-2027` / `…-2028`)
- Hand-edited student-facing README tables
- Mentioning the other radar product in the public README

### Slice order (locked)

| Session | Slice | Outcome |
|---------|-------|---------|
| **1 (this)** | Slice 1 | Valid empty catalog: `make lint test validate` green |
| 2 | Slice 2 | Generator-owned README; 12 program-fallback seeds; real Apply URLs |
| 3 | Slice 3 | Shared inclusion classifier |
| 4 | Slice 4 | Scraper framework + first non-Workday adapter |
| 5 | Slice 5–6 | Archive, daily refresh PR, issue template; T6.2 publish bar |

Do not combine Slice 1 and Slice 4 in one engineer session.

### Slice 1 done (PM signs off)

PLAN.md **Done when:** `make lint test validate` is green on Windows and a Unix-like shell; namespace UUID is documented and **not** the program-catalog namespace.

Plus HANDOFF AC on T0.1–T0.3 and T1.1–T1.3 (checklist below). Engineers do not self-declare Slice 1 done.

---

## Slice 1 tickets (open now)

Source: HANDOFF Epic 0 + Epic 1. Implement in this order. All are AFK except T1.2 namespace UUID (document in ADR; do not reuse another catalog’s namespace).

### T0.1 — License, git hygiene, Python project

**Epic:** 0 — Repo bootstrap  
**Blocked by:** None — can start immediately

**What to build:** Dual license files, project metadata, Makefile targets, and a requirements layout so `lint` / `test` / `validate` exist as commands. `e2e` may be a stub.

**Work:** MIT `LICENSE.md`; CC-BY `LICENSE-DATA.md` (or `data/LICENSE`); `NOTICE`; `.gitignore`; `pyproject.toml` / `requirements.txt` / `requirements-dev.txt`; Makefile targets `lint`, `format`, `test`, `validate`, `e2e`.

**Acceptance (HANDOFF):**

- [ ] Dual license documented in README footer (do not hand-edit a listings table)
- [ ] `python -m compileall` / Ruff runnable
- [ ] No secrets committed

**Slice 1 note:** If Windows has no `make`, document the equivalent Python invocations (already sketched in AGENTS.md). Makefile still required so Unix CI can use the same names later.

---

### T0.2 — Agent + domain docs (ADRs 0001–0003)

**Epic:** 0  
**Blocked by:** None (can land with T0.1)

**What to build:** ADRs that lock license split, internship ID namespace, and maintainer-managed catalog JSON. Keep AGENTS.md / CONTEXT.md aligned with HANDOFF (already seeded).

**Work:** `docs/adr/0001-dual-license.md`, `0002-internship-ids-uuid-v5.md`, `0003-maintainer-managed-catalog.md`.

**Acceptance (HANDOFF):**

- [ ] ADRs match locked decisions (new ID namespace; no hand-edit JSON)
- [ ] AGENTS.md forbids copying program scrapers and forbids mentioning the other radar product in the public README

---

### T0.3 — `config/current_season.json`

**Epic:** 0  
**Blocked by:** T0.1 (project layout)

**What to build:** Maintainer season flag `{ "season": "summer-2027" }`. Season is a field on rows; this file is the README default later. Do not create a new repo for 2028.

**Acceptance (HANDOFF):**

- [ ] File exists with `summer-2027`
- [ ] Changing the file does not require a code change

**Parked until Slice 2:** “Generator reads this for which season’s active table to lead with.” Do not implement the generator in this session.

---

### T1.1 — `data/schema.json` + `docs/SCHEMA.md`

**Epic:** 1 — Schema, IDs, validation  
**Depends on:** T0.1

**What to build:** Internship-native JSON Schema and docs. Empty catalogs are valid.

**Required fields (HANDOFF §5):** `id`, `company`, `title`, `apply_url`, `season`, `role_family`, `location`, `degree`, `row_kind`, `source`, `first_seen`, `last_seen`

**Enums:**

- `row_kind`: `posting` \| `program_fallback`
- `role_family`: Software; BME/R&D; Electrical/firmware; Mechanical/robotics; Data/ML; Quality/manufacturing; Other STEM
- `degree`: `bs` \| `ms` \| `bs_ms` \| `unspecified`
- `source`: `scrape` \| `seed` \| `issue`
- `season`: at least `summer-2027`; allow future seasons

**Acceptance (HANDOFF):**

- [ ] Required fields from HANDOFF §5
- [ ] Enums for `role_family`, `row_kind`, `season`, `degree`, `source`
- [ ] Example fixture with one `posting` and one `program_fallback` (test fixture, not a hand-edited README table)

---

### T1.2 — `scripts/internship_ids.py` (TDD)

**Epic:** 1  
**Depends on:** T1.1

**What to build:** Deterministic UUID v5 identity. Test first.

**Identity (locked):**

1. If `req_id` present → `company|req_id`
2. Else if apply URL present → `company|canonical_url` (strip `utm_*` / tracking; never raw Workday search URLs)
3. Else `company|normalized_title|normalized_location`
4. Program fallback: `company|program_url`
5. UUID v5 of that key in **this repo’s** namespace

**Acceptance (HANDOFF + PLAN):**

- [ ] Layered key tests: `req_id` wins; URL canonicalization strips `utm_*` / session-looking params; program_url path
- [ ] Same inputs → same UUID; different companies → different IDs
- [ ] Namespace UUID is unique to this catalog (documented in ADR 0002)
- [ ] Namespace is **not** the program-catalog namespace

---

### T1.3 — `scripts/validate_data.py`

**Epic:** 1  
**Depends on:** T1.1

**What to build:** Schema gate for `data/active/internships.json` and `data/archived/internships.json`. Bootstrap with empty `[]` files.

**Acceptance (HANDOFF + PLAN):**

- [ ] Validates active + archived JSON
- [ ] Fails on schema miss, duplicate `id`, missing `apply_url`
- [ ] Empty `[]` catalogs are valid
- [ ] `make validate` (or documented Python equivalent) is green

**Test order (PLAN):**

1. UUID v5 is stable for the same `company|req_id`
2. `req_id` wins over URL; canonical URL strips `utm_*`; program fallback uses `company|program_url`
3. Validator accepts `[]`; rejects missing `apply_url`, bad enums, duplicate `id`

---

## Ready, not started (Slice 2+)

Do not pick these up in the Slice 1 session.

| Slice | HANDOFF tickets | Status |
|-------|-----------------|--------|
| 2 | T2.1, T2.2, T3.1, T3.2 | Ready, not started |
| 3 | T3.3 | Ready, not started |
| 4 | T4.1, T4.2, T4.4 | Ready, not started |
| 5 | T2.3, T5.1, T5.2 | Ready, not started |
| 6 | T4.3, T6.1, T6.2 | Ready, not started |

v1 is not done until PM/owner ticks HANDOFF **T6.2**.

---

## Slice 1 engineer prompt (paste into a new agent session)

```text
Implement Slice 1 from PLAN.md using TDD for internship IDs and validate.

You are the Slice 1 engineer for medtech-internship-radar-catalog. PM owns sequence and acceptance. Do not declare Slice 1 done yourself.

Read in order: PLAN.md (Slice 1 only), HANDOFF.md (T0.1–T0.3, T1.1–T1.3 and §5 record shape), CONTEXT.md, AGENTS.md, docs/pm/SLICE-1-KICKOFF.md.

Build only Slice 1:
- Dual license (MIT code, CC-BY 4.0 data/), NOTICE, pyproject.toml, requirements, Makefile (lint, format, test, validate; e2e may stub)
- config/current_season.json = { "season": "summer-2027" }
- ADRs 0001–0003 (dual license, UUID v5 namespace unique to this catalog, maintainer-managed JSON)
- data/schema.json + docs/SCHEMA.md (internship-native; required fields and enums from HANDOFF §5)
- Empty data/active/internships.json and data/archived/internships.json as []
- scripts/internship_ids.py — TDD first
- scripts/validate_data.py
- Python 3.9+ compatible; Ruff; pytest

Identity rules to test:
1. UUID v5 is stable for the same company|req_id
2. req_id wins over URL; canonical URL strips utm_* ; program fallback uses company|program_url
3. Validator accepts []; rejects missing apply_url, bad enums, duplicate id
4. Namespace UUID is documented and is not the program-catalog namespace

Done when: make lint test validate is green (Windows and Unix-like). If make is missing on Windows, also document python -m equivalents and still add the Makefile.

Do not:
- Implement generate_dashboard.py, assets/apply.svg, or README tables
- Add scrapers, allowlist hub URL research, or GitHub Actions
- Hand-edit a student-facing README table
- Import program scrapers or the program schema from the pattern repo in HANDOFF.md
- Mention the other radar product in the public README
- Filter by work_auth / visa
- Add companies beyond the locked twelve
- Create a 2027/2028 cycle repo
- Use live network in tests

Copy skeleton habits only (schema gate, dual license, no hand-edit catalog JSON). Use the tdd skill. Use context7-mcp for jsonschema / pytest / ruff if you need current docs.
```

---

## Slice 1 acceptance checklist (PM)

Sign off only when all are true.

### PLAN.md Done when

- [ ] `make lint` green (Ruff + compileall)
- [ ] `make test` green
- [ ] `make validate` green
- [ ] Commands work on Windows; Makefile exists for Unix-like shells
- [ ] Internship ID namespace UUID documented in ADR 0002 and is not the program-catalog namespace

### Ticket AC

- [ ] T0.1 Dual license files + README footer; no secrets
- [ ] T0.2 ADRs 0001–0003; AGENTS.md boundaries still hold
- [ ] T0.3 `config/current_season.json` is `summer-2027`
- [ ] T1.1 Schema + SCHEMA.md + posting and program_fallback fixture
- [ ] T1.2 Identity tests (req_id wins, URL canonicalization, program_url path, stability)
- [ ] T1.3 Empty `[]` valid; missing apply_url / bad enum / duplicate id fail; active + archived validated

### Scope guard

- [ ] No generator, no Apply badge, no scrapers, no Actions
- [ ] Public README has no listings table and no other-radar brand mention
- [ ] Catalog JSON is empty `[]` (or test fixtures only, not a hand-maintained 12-row README)

---

## Blockers and risks

| Item | Blocks | Action |
|------|--------|--------|
| Repo has **no git remote** and **no commits yet** | GitHub Issues, Actions, refresh-via-PR | Owner creates GitHub repo when ready. Slice 1 does not need a remote. Tickets live in this packet until Issues exist. |
| **No CI** until Slice 1 lands (and Actions are Slice 5) | Automated gate | Slice 1 acceptance is local `make lint test validate`. Do not start daily refresh now. |
| Intern hub URLs not researched | Slice 2 Apply links | **Not a Slice 1 blocker.** Research during Slice 2 (T3.1). Wrong URLs fail Slice 2 acceptance. |
| Windows `make` may be missing | PLAN “Unix-like shell” line | Engineer ships Makefile + Python fallbacks. PM may waive local `make` if Python targets pass; do not invent CI in Slice 1. |
| Pattern-repo namespace collision | T1.2 | Engineer must generate a **new** UUID v5 namespace and document it. |

---

## Parked (out of v1 / later slices)

- Website `medtech-internship-radar`
- J&J / Siemens / Philips / Penumbra / Align as allowlist (candidates only)
- Visa column or sponsorship filter
- Cycle repos
- Workday adapters before a 12-row generated README exists
