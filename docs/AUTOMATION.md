# Automation

Daily catalog work is **refresh via pull request**. Listings JSON and generated README files are never pushed straight to `main`. This repo may not have a GitHub remote yet; the workflow YAML is still the intended habit once Actions can run.

Pipeline: **scrape → validate → archive → generate README**.

## Local dry-run (mocked HTTP)

Uses the Boston Scientific Eightfold fixture against **temp copies** of the catalog. Never merge `--fixture` into `data/active/internships.json` — that writes synthetic job IDs as if they were live postings.

```bash
python -m pytest tests/test_refresh_catalog.py tests/test_cli.py -q
```

Or the Makefile target:

```bash
make e2e
```

If `make` is unavailable (typical on Windows PowerShell):

```bash
python -m pytest tests/test_refresh_catalog.py tests/test_cli.py -q
```

`--fixture` is for mocked-HTTP tests only. Pass `--catalog` (and `--archived` / `--readme` / `--inactive` / `--newest` / `--health` / `--artifact`) to temp files if you invoke `refresh_catalog.py --fixture` yourself. A live sweep is:

```bash
python -m scripts.refresh_catalog
```

That live command:

1. Scrapes allowlisted adapters (no fixture) into `data/active/internships.json`
2. Validates active + archived catalogs
3. Probes apply URLs and archives ATS-closed / two-miss / dead program-URL rows
4. Restores a program-fallback seed if a company has zero active rows
5. Writes `data/health.json`, `README.md`, `README-Inactive.md`, and `README-Newest.md`

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

```bash
python -m scripts.archive_closed --force-close <internship-id>
python -m scripts.generate_dashboard
```

Do **not** push the dry-run listing changes to `main`. Open a refresh PR (below) or discard the local diff.

## Daily GitHub Action

Workflow: [`.github/workflows/daily-catalog-refresh.yml`](../.github/workflows/daily-catalog-refresh.yml)

On a schedule (and `workflow_dispatch`) it runs a live `python -m scripts.refresh_catalog`, commits to `automation/daily-catalog-refresh`, and opens or updates an **open** PR against `main`. It explicitly dispatches CI for the generated commit, waits for the checks to pass, then squash-merges the PR and deletes the refresh branch. A failed CI run leaves the PR open for inspection. It never `git push`es listings to `main`.

If this repository has no GitHub remote yet, add the YAML anyway; enable the workflow after `origin` exists.

## CI on that PR

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

Pull requests to `main` (including the daily refresh PR) run `pytest` and `python -m scripts.validate_data`. Tests use mocked HTTP only. CI does not scrape live ATS endpoints.

```bash
python -m pytest -q
python -m scripts.validate_data
```
