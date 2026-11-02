# Documentation reconciliation verification — 2026-10-19

This record separates checked implementation, published data, historical source
observations, and remaining acceptance. Current contributor guidance is in
[PLAN](../../PLAN.md), [CURRENT-SLICE](../pm/CURRENT-SLICE.md),
[DEVELOPMENT](../DEVELOPMENT.md), and [AUTOMATION](../AUTOMATION.md).

## Revision and evidence boundary

Checked on 2026-10-19 (America/Los_Angeles), based on commit
`1c2783985f04fb8391cdc38e6be700fc57aca41b`, with an already dirty working tree.
Pre-existing command/eligibility/archive changes and their tests were preserved;
local results include those changes, not just committed main. No claim here says
those working-tree changes have been published. No live scraper sweep or listing
cleanup was run for this documentation task. Catalog JSON was not changed.

The original [HANDOFF](../../HANDOFF.md) T6.2 sign-off (2026-08-14), 12-company
baseline, and no-remote waiver remain historical. Approved expansion to 32 is
recorded in [CURRENT-SLICE](../pm/CURRENT-SLICE.md) and implemented in the
[allowlist](../../config/allowlist.json). Completed bootstrap instructions are
retained as historical material, not remaining tasks.

## Scope and published snapshot

| Check | Observed result | Evidence |
|---|---|---|
| Approved companies | 32 | [allowlist](../../config/allowlist.json); original 12 + 5 wave 1 + 15 wave 2 |
| Scraper implementation | 32 registered companies; registry names equal allowlist names | `discover_scrapers()` in [framework](../../scripts/scraper_framework.py), company modules, mocked adapter tests |
| Default season | `summer-2027` | [season configuration](../../config/current_season.json) |
| Published active snapshot | 117 rows: 100 postings from 15 companies, 17 fallback hubs; 32 represented companies | [active data](../../data/active/internships.json) at base commit |
| Recorded sweep health | `2026-10-19`; updated count 78; Medtronic failed; archived count 31 | [health](../../data/health.json) at base commit |

These mutable file links should be read at the base commit for these exact counts.
Updated count is the implementation's count of rows with `last_seen` equal to the
sweep date, not an independently verified count of changed/eligible jobs. Fallback
hubs are navigation coverage, not proof of open internships. Posting rows can
predate the new eligibility gate and need reviewed cleanup.

## Observed GitHub operations

Read-only GitHub inspection confirmed a configured `origin` and these dated results:

- [Daily refresh run 39292344683](https://github.com/BrianLiDesign/medtech-internship-radar-catalog/actions/runs/39292344683),
  created 2026-10-19 17:14:01 UTC: success, starting at `d29d5d4`.
- [Refresh PR #15](https://github.com/BrianLiDesign/medtech-internship-radar-catalog/pull/15):
  merged 2026-10-19 17:17:42 UTC as the base commit above.
- [Dispatched CI run 39292798929](https://github.com/BrianLiDesign/medtech-internship-radar-catalog/actions/runs/39292798929):
  success on refresh commit `3968daffa54477216e12512d93d54b93072571f1`.
- [PR-event CI run 39292802136](https://github.com/BrianLiDesign/medtech-internship-radar-catalog/actions/runs/39292802136):
  failure on the same refresh commit; the API returned an empty jobs list. Its cause
  was not established in this task. A successful dispatch does not erase this failure.

The [refresh workflow](../../.github/workflows/daily-catalog-refresh.yml) configures
02:00 UTC daily and manual dispatch, branch `automation/daily-catalog-refresh`,
open/update PR, explicit CI dispatch for the generated commit, wait, then squash
merge guarded by that commit SHA and branch deletion. No-change runs skip those
steps. Repository permissions/policies and source availability can still fail future
runs. CI is configured for Python 3.9/3.13 with mocked HTTP; the live refresh is a
separate workflow, not a live-network test in CI.

## Local command verification

Python **3.13.15**, Windows PowerShell, repository root. `make` was unavailable;
the exact Python equivalents of [Makefile](../../Makefile) targets were run using
the reviewed [.project-check.json](../../.project-check.json). All exited zero:

| Target | Executed command | Result |
|---|---|---|
| lint | `python -m ruff check scripts tests config/scrapers` | Passed |
| lint | `python -m ruff format --check scripts tests config/scrapers` | 87 files already formatted |
| lint | `python -m compileall -q scripts config/scrapers` | Passed |
| test | `python -m pytest -q` | 340 passed |
| validate | `python -m scripts.validate_data` | Catalog validation passed |
| e2e | `python -m pytest tests/test_refresh_catalog.py tests/test_cli.py -q` | 12 passed |
| generate | `python -m scripts.generate_dashboard` | All three views generated; only landing README prose/links changed |

The runner recorded no source changes during its run and no truncated outputs.
Its local JSON report is outside the repository in the user's temporary directory
(`medtech-docs-check-2026-10-19.json`); this table is the durable reviewed summary.
The CLI tests cover repository-root module entrypoints without a `PYTHONPATH`
override. The command repair is also recorded in
[PR #14](https://github.com/BrianLiDesign/medtech-internship-radar-catalog/pull/14).
Python 3.9 and a Unix shell were not rerun locally. Setup is documented from the
requirements files; a fresh environment install was not performed for this audit.
Live `refresh_catalog`, issue writes, force-close writes, and seed restoration were
verified through source and mocked/temp-file tests, not executed against published data.

## Final behavior from the command, eligibility, and archive handoffs

1. **Commands:** repository-root `python -m scripts.*`; Makefile and workflow
   commands use that form. `make e2e` runs temporary-output refresh and CLI tests.
   Fixture ingestion refuses the production active path; manual fixture refresh
   must redirect all outputs to temporary paths. The test target is the safer recipe.
2. **Eligibility:** [ELIGIBILITY](../ELIGIBILITY.md) and
   [shared gate](../../scripts/inclusion.py) define affirmative US/STEM evidence,
   title/term/year checks, BS/MS versus doctoral-only rules, and allowed missing
   degree/term evidence. Co-ops need affirmative summer evidence; sponsorship and
   returning/internal tags are descriptive. Requested ingestion season propagates
   through the gate; a parsed source season is evidence. This is a text heuristic,
   not a guarantee about unrequested detail-page requirements. Issue imports still
   require independent maintainer eligibility review.
3. **Archive:** [AUTOMATION](../AUTOMATION.md#archive-evidence-and-restoration) and
   [SCHEMA](../SCHEMA.md#daily-archive-transitions) document adjacent-date misses,
   same-day idempotence, failed-company preservation, definitive closure, 404/410
   fallback deaths, inconclusive probes, and archived-fallback restoration blocks.
   The standalone archive CLI has no live probe session and can sweep other rows
   while applying explicit force-close IDs.

## Remaining limitations and follow-up

- Submit a separate reviewed maintainer cleanup PR for existing ineligible postings;
  preserve original IDs/URLs/first-seen dates, record source reasons, validate, and
  regenerate views. The classifier alone does not remove existing rows.
- Investigate current recorded failures and the PR-event CI failure. Recheck live
  sources when making new availability claims. Historical August observations in
  [CURRENT-SLICE](../pm/CURRENT-SLICE.md#historical-source-observations) are not
  October verification of those endpoints.
- No live Apply URL audit, fresh install, or full all-company source verification
  was performed. Thirty-two registered scrapers is implementation coverage only.
- README prose was changed in [the generator](../../scripts/generate_dashboard.py)
  and regenerated. Public README variants and student-facing docs were checked for
  prohibited cross-brand text; internal historical design references remain internal.

Final documentation checks: local Markdown link targets exist across the edited
planning/operations documents; an explicit brand scan passed across all three
README views and eight public contribution/operations/evidence documents. Active,
archived, and health JSON match HEAD after line-ending normalization. The landing
README matches generator output for 2026-10-19. `git diff --check` passed.
