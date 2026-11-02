# Automation

Daily catalog work is **refresh via pull request**. Listings JSON and generated README files are never pushed straight to `main`. The GitHub remote and workflows exist. The current approved scope is 32 companies;
the default ingestion/README season is `summer-2027`. See the
[2026-10-19 verification record](verification/2026-10-19-documentation.md) for observed
refresh/CI results and limitations.

Pipeline: **scrape → validate → archive → generate README**, computed in staging and validated before recoverable publication. See [refresh safety and recovery](REFRESH-SAFETY.md) for catalog invariants, rollback, standalone maintenance, and failure diagnostics.

## Local dry-run (mocked HTTP)

Uses the Boston Scientific Eightfold fixture against **temp copies** of the catalog. Never merge `--fixture` into `data/active/internships.json` — that writes synthetic job IDs as if they were live postings.

```bash
python -m pytest tests/test_refresh_catalog.py tests/test_refresh_safety.py tests/test_cli.py tests/test_qualification_refresh.py -q
```

Or the Makefile target:

```bash
make e2e
```

If `make` is unavailable (typical on Windows PowerShell):

```bash
python -m pytest tests/test_refresh_catalog.py tests/test_refresh_safety.py tests/test_cli.py tests/test_qualification_refresh.py -q
```

`--fixture` is for mocked-HTTP tests only. Pass `--catalog` (and `--archived` / `--readme` / `--inactive` / `--newest` / `--health` / `--artifact`) to temp files if you invoke `refresh_catalog.py --fixture` yourself. A live sweep is:

```bash
python -m scripts.refresh_catalog
```

That live command:

1. Scrapes allowlisted adapters (no fixture) into `data/active/internships.json`
2. Validates active + archived catalogs
3. Probes apply URLs and archives ATS-closed / two-miss / dead program-URL rows
4. Restores approved fallback seeds for companies with zero active rows, unless an archived fallback blocks restoration for that company/season or the seed ID is already archived
5. Writes `data/health.json`, `README.md`, `README-Inactive.md`, and `README-Newest.md`

## Archive evidence and restoration

The [archive implementation](../scripts/archive_closed.py),
[seed restoration](../scripts/apply_seeds.py), and [SCHEMA](SCHEMA.md#daily-archive-transitions)
are the behavior references:

- Posting: explicit ATS closure, HTTP 404/410, or reviewed force-close archives
  immediately. Otherwise two discovery misses on adjacent calendar dates archive.
- `last_miss_on` counts a miss at most once per date. Gaps reset the streak to one;
  legacy undated counts cannot establish the previous day's failure. Dates come
  from the refresh sweep date (or explicit `--today`), not a rolling 24-hour timer.
- An unavailable company scraper preserves posting miss state unless an apply probe
  provides definitive closure. A rediscovered posting resets its miss evidence.
- During the archive step, a posting present in both catalogs is reconciled by ID:
  its earliest `first_seen` is preserved, old closure fields are removed, and it
  remains in only one catalog. A later closure replaces its archived record rather
  than appending a duplicate. The archive stores the latest closure per posting ID.
- Fallback: only 404/410 counts as a URL death; two adjacent dates are required.
  A 2xx resets evidence. Timeouts, 429, 5xx, denied access, and unresolved redirects
  neither add a miss nor prove health.
- Archived fallback closures block automatic restoration for that company/season,
  even if the seed URL changes. Reopening requires maintainer intervention. Coverage
  targets do not authorize resurrecting a closed hub to force 32 active companies.

The standalone `archive_closed` CLI has no HTTP probe session. It applies stored
last-seen/miss evidence and explicit force-close IDs, and performs the regular sweep
as well. Live URL probes happen in `refresh_catalog`. Review all changes from a
standalone force-close; it is not limited to the named ID. Validate afterward.

## Merge an issue into the catalog

Community reqs arrive as structured issues. Maintainers merge them locally
(identity + schema, `source: issue`). Duplicate internship IDs are skipped.
See [CONTRIBUTING.md](../CONTRIBUTING.md).

```bash
python -m scripts.merge_issue \
  --company "Medtronic" \
  --title "Software Engineer Intern" \
  --location "Minneapolis, MN" \
  --apply-url "https://example.com/job/R-12345" \
  --degree Unspecified \
  --season summer-2027 \
  --req-id R-12345
python -m scripts.generate_dashboard
```

Use `--dry-run` to print the row without writing. Do not accept raw listings-JSON PRs from the community.

Force-close a row (maintainer / issue):

For a reviewed eligibility correction, follow the evidence and cleanup process
in [ELIGIBILITY.md](ELIGIBILITY.md#existing-active-rows-reviewed-maintainer-cleanup).
Classifier changes alone do not immediately remove existing active rows.

```bash
python -m scripts.archive_closed --force-close <internship-id>
python -m scripts.validate_data
python -m scripts.generate_dashboard
```

A true `--dry-run` writes no listing changes. Submit reviewed maintainer writes via PR;
do **not** push listing changes directly to `main`. Open a refresh PR (below) or discard the local diff.

## Daily GitHub Action

Workflow: [`.github/workflows/daily-catalog-refresh.yml`](../.github/workflows/daily-catalog-refresh.yml)

On a schedule (and `workflow_dispatch`) it runs a live `python -m scripts.refresh_catalog`, commits to `automation/daily-catalog-refresh`, and opens or updates an **open** PR against `main`. It explicitly dispatches CI for the generated commit, waits for the checks to pass, then squash-merges the PR and deletes the refresh branch. A failed CI run leaves the PR open for inspection. It never `git push`es listings to `main`.

The configured schedule is **02:00 UTC daily**, plus manual dispatch. Schedule
configuration does not guarantee exact execution time. Inspect the Actions run and
refresh PR when the health date is stale or a run fails. No-change sweeps skip PR/CI/
merge steps. Merge depends on repository permissions and branch policies; a failure
requires inspection, not a direct push to `main`.

The workflow dispatches `ci.yml` for the refresh branch and identifies the run using
the generated commit SHA. Merge uses `--match-head-commit` for that SHA. See the
[dated observed refresh and CI outcomes](verification/2026-10-19-documentation.md).

## CI on that PR

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

Pull requests to `main`, pushes to `main`, and manual CI dispatch are configured to
run Ruff lint/format, compileall, pytest, and catalog validation on Python 3.9 and
3.13. The refresh path explicitly dispatches that CI workflow. Tests use mocked HTTP only. CI does not scrape live ATS endpoints.

```bash
python -m pytest -q
python -m scripts.validate_data
```
