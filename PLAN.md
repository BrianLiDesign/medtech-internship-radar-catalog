# Development plan — next steps

**Status:** Ready to implement  
**Locked product spec:** [HANDOFF.md](HANDOFF.md) (do not reopen)  
**Terms:** [CONTEXT.md](CONTEXT.md)

This file is the **build order**. HANDOFF is the backlog and decision log. Do not start scrapers, Workday adapters, or GitHub Actions until Slice 2’s README exists.

## Where we are

The repo is docs-only: `HANDOFF.md`, `AGENTS.md`, `CONTEXT.md`, stub `README.md`, `.gitignore`. No Python, schema, CI, or listings yet.

First shippable increment: **a generated README that lists all 12 companies with Apply badges**, even if every row is a program-fallback seed. That is the v1 publish bar’s minimum. Posting-level scrapers come after.

## How to build

Vertical slices, test-driven on catalog behavior (IDs, validate, generator, inclusion, archive). Mock HTTP in CI. One slice green before starting the next.

Copy **habits** from the sibling catalog (schema gate, allowlist, generated README, refresh-via-PR). Do **not** copy program scrapers, program schema, or a 60-day SLO.

---

## Slice 1 — Repo that can say “this JSON is valid”

**Goal:** `make lint test validate` works on an empty catalog.

| Do | Don’t yet |
|----|-----------|
| Dual license files, `pyproject.toml`, requirements, Makefile, `config/current_season.json` | Scrapers, README tables, live fetches |
| `data/schema.json` + empty `data/active/internships.json` / `data/archived/internships.json` | Hand-written student-facing README tables |
| `scripts/internship_ids.py` + `scripts/validate_data.py` | GitHub Actions daily job |
| ADRs 0001–0003 (license, UUID v5 namespace, maintainer-managed JSON) | Website |

**Behaviors to test (in this order):**

1. UUID v5 is stable for the same `company|req_id`.
2. `req_id` wins over URL; canonical URL strips `utm_*`; program fallback uses `company|program_url`.
3. Validator accepts `[]`; rejects missing `apply_url`, bad enums, duplicate `id`.

**Done when:** `make lint test validate` is green on Windows and a Unix-like shell; namespace UUID is documented and **not** the program-catalog namespace.

**HANDOFF tickets:** T0.1–T0.3, T1.1–T1.3.

---

## Slice 2 — Students can scan 12 Apply links

**Goal:** Generator owns the README. Fixture/seeds produce all 12 companies.

| Do | Don’t yet |
|----|-----------|
| `assets/apply.svg` | ATS adapters |
| `scripts/generate_dashboard.py` | Close/archive automation |
| Maintainer seed path that emits 12 `program_fallback` rows (script or checked-in seed **input**, not a hand-edited README) | Issue template / contribution community loop |
| Jump links by `role_family`; columns Company \| Role \| Location \| Degree \| Apply \| Age | Visa column, Inactive.md (stub OK) |

**Behaviors to test:**

1. Unspecified degree renders as `BS/MS`.
2. Age uses `posted_at` if set, else `first_seen`.
3. No `apply_url` → row omitted (seeds must all have URLs).
4. Empty role families omitted; current season comes from `config/current_season.json`.
5. Apply cell is the in-repo badge, not a hotlinked image.

**Hub URL research (needed for seeds):** For each of the 12, find the public university/intern careers page. If a URL is wrong, the Apply button is a lie. Record suspected ATS on the allowlist notes, but do not block Slice 2 on Workday.

**Done when:** `python scripts/generate_dashboard.py` writes a discover-first README; all 12 names appear; `make test validate` still green. This is the first commit that looks like a radar.

**HANDOFF tickets:** T2.1–T2.2, T3.1–T3.2 (seeds + allowlist URLs).

---

## Slice 3 — Inclusion rules as code

**Goal:** Shared classifier so later scrapers do not each invent “what counts.”

**Behaviors to test with title/location strings:**

- STEM in (including regulatory/quality intern); HR/marketing out
- Intern or summer co-op in; fall-only / multi-term rotation out
- PhD-only and new-grad FT out; “undergraduate or graduate” in
- US and US-remote in; non-US out

**Done when:** One module (e.g. `scripts/inclusion.py`) is the only place scrapers ask “keep this req?” Unit tests cover the cases above.

**HANDOFF tickets:** T3.3.

---

## Slice 4 — Hybrid ingest (thicken postings)

**Goal:** Framework + posting rows where the ATS is easy; Workday stays on fallback.

1. Internship-native base scraper (timeouts, rate limit, soft-fail, no invented rows).
2. Confirm ATS per company from Slice 2 notes — implement **Greenhouse/Lever/JSON only** for companies that actually use them.
3. Upsert by internship ID: `first_seen` frozen, `last_seen` updated, `source: scrape`.
4. Multi-city: explode only if apply URLs differ.

**Done when:** At least **one** company has real `posting` rows from a mocked (and optionally local live) scrape, merged without duplicating IDs; the other eleven may remain fallback. Daily Action is still later.

**HANDOFF tickets:** T4.1–T4.2, T4.4 (work_auth / returning tags, best-effort).

---

## Slice 5 — Rows can die honestly

**Goal:** Closed postings leave the main table; daily work is a PR, not a push to `main`.

- Archive on ATS-closed **or** two consecutive misses; program-fallback needs two URL deaths or a force-close
- `README-Inactive.md` (or below-the-fold archive) generated, not hand-edited
- GitHub Action: scrape → validate → archive → generate README → **open PR**
- Health strip: last sweep, updated count, failed scrapers, archived count

**Done when:** Tests prove the grace period; a dry-run workflow (or documented local equivalent) opens a refresh PR.

**HANDOFF tickets:** T2.3, T5.1–T5.2.

---

## Slice 6 — Public catalog hygiene

**Goal:** Others can add a req without touching JSON.

- Structured “Add internship” issue template (company dropdown = the 12)
- Maintainer merge script/docs (`source: issue`)
- CONTRIBUTING, SECURITY, scraper checklist, `candidates.json` for J&J / Siemens / Philips / Penumbra / Align
- Public README still must **not** mention the other radar product

**Done when:** Owner checklist in HANDOFF T6.2 passes (12 Apply URLs, generator-owned tables, daily PR path once, no brand cross-links).

**HANDOFF tickets:** T4.3, T6.1–T6.2.

---

## Explicitly later (not next)

- `medtech-internship-radar` website
- Deep Workday adapters for all 12
- Extra companies, off-season, new-grad, 2028 default season
- Shared package with the other catalog
- Alerts, Pages, Slack

---

## Suggested session cadence

| Session | Slice | Prompt for the next agent |
|---------|-------|---------------------------|
| 1 | Slice 1 | “Implement Slice 1 from PLAN.md using TDD for internship IDs and validate.” |
| 2 | Slice 2 | “Research the 12 intern hub URLs, add seeds, implement the README generator.” |
| 3 | Slice 3 | “TDD the inclusion classifier.” |
| 4 | Slice 4 | “Add the scraper framework and the first non-Workday adapter.” |
| 5 | Slice 5–6 | “Archive rules, daily refresh PR, issue template.” |

Do not combine Slice 1 and Slice 4 in one session. The README with 12 fallbacks is the milestone that unblocks everything else.
