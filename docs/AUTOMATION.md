# Automation

Daily catalog work is **refresh via pull request**. Listings JSON and generated README files are never pushed straight to `main`. This repo may not have a GitHub remote yet; the workflow YAML is still the intended habit once Actions can run.

Pipeline: **scrape → validate → archive → generate README**.

## Local dry-run (mocked HTTP)

Uses the Boston Scientific Eightfold fixture. No live ATS, Workday, or GitHub (`gh`) calls.

```bash
python scripts/refresh_catalog.py --fixture tests/fixtures/boston_scientific_pcsx.json
```

Or the Makefile target:

```bash
make e2e
```

If `make` is unavailable (typical on Windows PowerShell):

```bash
python scripts/refresh_catalog.py --fixture tests/fixtures/boston_scientific_pcsx.json
```

That command:

1. Merges fixture postings into `data/active/internships.json` (no live network)
2. Validates active + archived catalogs
3. Applies archive rules (ATS-closed, two consecutive posting misses, two program-URL deaths, or `--force-close`)
4. Writes `data/health.json`, `README.md`, and `README-Inactive.md`

## Merge an issue into the catalog

Community reqs arrive as structured issues. Maintainers merge them locally
(identity + schema, `source: issue`). Duplicate internship IDs are skipped.
See [CONTRIBUTING.md](../CONTRIBUTING.md).

```bash
python scripts/merge_issue.py \
  --company "Medtronic" \
  --title "Software Engineer Intern" \
  --location "Minneapolis, MN" \
  --apply-url "https://example.com/job/R-12345" \
  --degree Unspecified \
  --season summer-2027 \
  --req-id R-12345
python scripts/generate_dashboard.py
```

Use `--dry-run` to print the row without writing. Do not accept raw listings-JSON PRs from the community.

Force-close a row (maintainer / issue):

```bash
python scripts/archive_closed.py --force-close <internship-id>
python scripts/generate_dashboard.py
```

Do **not** push the dry-run listing changes to `main`. Open a refresh PR (below) or discard the local diff.

## Daily GitHub Action

Workflow: [`.github/workflows/daily-catalog-refresh.yml`](../.github/workflows/daily-catalog-refresh.yml)

On a schedule (and `workflow_dispatch`) it runs a live `python scripts/refresh_catalog.py`, commits to `automation/daily-catalog-refresh`, and opens or updates a PR against `main`. It never `git push`es listings to `main`.

If this repository has no GitHub remote yet, add the YAML anyway; enable the workflow after `origin` exists.

## CI on that PR

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

Pull requests to `main` (including the daily refresh PR) run `pytest` and `python scripts/validate_data.py`. Tests use mocked HTTP only. CI does not scrape live ATS endpoints.

```bash
python -m pytest -q
python scripts/validate_data.py
```
