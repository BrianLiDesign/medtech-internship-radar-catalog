# ADR-0003: Maintainer-managed catalog JSON

## Status

Accepted

## Context

Allowing contributor PRs to hand-edit `data/active/internships.json` or
`data/archived/internships.json` risks inconsistent records, merge conflicts
with automation, skipped identity rules, and bypassed schema validation.

## Decision

- Catalog JSON is modified only by maintainers or the automation pipeline
  (refresh PRs), never by community listing edits.
- Community contributions use structured issues for reqs and PRs for
  scrapers / allowlist changes.
- `scripts/validate_data.py` is the schema gate. Empty `[]` catalogs are
  valid so bootstrap can land before seeds exist.
- Changing an existing internship `id` requires an explicit migration plan.

## Consequences

- Higher data consistency and a single identity function.
- Contributors use `.github/ISSUE_TEMPLATE/add-internship.yml` for reqs and
  PRs for scrapers / allowlist. Maintainers merge issues with
  `scripts/merge_issue.py` (`source: issue`, identity + schema, no duplicate IDs).
- Validated community PRs against listings JSON are not a v1 path.
