# Refresh safety and recovery

Refresh computes active and archived catalogs, health metadata, and all three
README views in staging. Structural input validation and within-catalog ID
uniqueness run before mutation. Cross-catalog overlap is permitted at this phase
so posting rediscovery can be reconciled. Final validation requires unique and
disjoint catalog IDs, no closure metadata on active rows, and a valid closure date
and reason on every archived row. Final validation is the standalone validator's
default contract. Ambiguous same-catalog duplicate IDs fail rather than choosing
one record silently.

Rediscovered postings keep their earliest first-seen date and current details.
Reopened postings lose stale closure metadata; re-closure stores the latest closure
once per ID. This includes rediscovery after posting force-close. Archived fallback
hubs still require maintainer intervention before reopening. Existing daily-miss,
unavailable-company, and definitive URL-closure rules apply.

All six candidates must exist and pass validation before publication starts.
Generation and validation failures leave configured published outputs unchanged.
Publication writes a temporary sibling of each destination before replacing it,
with backups and a journal beside the active catalog named
`.internships.json.publication` for the standard catalog filename. The journal
records the exact ordered output destinations. Caught replacement failures roll
back the snapshot; interrupted promotion is rolled back on the next invocation.
A fully committed promotion only needs journal cleanup on restart.

Rerun the same command with the **same output destinations** to recover. Keep the
journal and backups if recovery fails, repair the storage/permission problem,
then rerun. A different output set fails with a recovery error; use the original
refresh or archive command first. Never manually delete a prepared journal to
force another sweep. Originally absent destinations are removed during rollback.
Keep one writer per output set; the daily workflow already serializes its runs.
This is recoverable replacement, not a simultaneous multi-file transaction or
protection against arbitrary filesystem corruption.

The standalone archive CLI uses the same input validation and protected publication
for its two catalog outputs. It has no HTTP probe session. A force-close invocation
also performs the normal archive sweep and must be reviewed as such.

## Failure evidence

With default paths, failed refreshes write `report.json` and
`candidate-preview.json` under `logs/scrape_failures-diagnostics/`. Custom scraper
artifact paths use a sibling directory named `<artifact-stem>-diagnostics`.
Reports identify the failed phase, attempted date, Actions commit when available,
validation error count, safe reason categories and implicated IDs, approved failed-scraper names, and
recovery guidance. Attempted dates never substitute for successful published health.

Candidate previews are **diagnostic projections**, not replayable catalogs: only
UUIDs, row kinds and parseable dates are retained, with a 10,000-row limit per
catalog. Raw descriptions, titles, URLs, exception messages, environment variables,
and authenticated request data are excluded to avoid exporting untrusted source
text or credentials. Reports mark candidates as not published. Raw scrape-failure
logs and publication backups stay local and are not uploaded.

The daily workflow uploads these two JSON diagnostics only after a failure and
retains the artifact for seven days. Find it under the failed Actions run's
Artifacts section. Early setup failures may produce no report. An upload failure
does not replace the original failing status. Local reports can describe an older
attempt; check their date. Diagnostics and journals are excluded from the explicit
catalog commit list and cannot become refresh PR inputs.

## Verification

Use temporary outputs and mocked HTTP, never production fixture ingestion:

```bash
python -m pytest tests/test_refresh_catalog.py tests/test_refresh_safety.py tests/test_cli.py tests/test_qualification_refresh.py -q
```

`make e2e` runs this same group. Tests exercise persisted output invariants, CLI
errors, repeated lifecycle transitions, generation failure, replacement failure,
interruption, rollback failure and restart recovery. Full verification also runs
Ruff, compileall, the full pytest suite and catalog validation. The CI matrix
remains Python 3.9 and 3.13; local Python results do not establish hosted CI success.
