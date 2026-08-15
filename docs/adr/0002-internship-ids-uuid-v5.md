# ADR-0002: Internship IDs as UUID v5

## Status

Accepted

## Context

Catalog rows need stable identifiers across scraper runs, seeds, and issue
merges. Changing an ID after a row is published breaks consumers. Identity
must be intern-posting native: req IDs and apply URLs, not program names.

This catalog must use its **own** UUID v5 namespace. Reusing another
catalog's namespace would collide IDs across datasets.

## Decision

- Canonical ID generation lives in `scripts/internship_ids.py`.
- Namespace UUID (this catalog only):

  `4f487264-223e-5db2-9177-b468a522ab4c`

  Derived as `uuid.uuid5(uuid.NAMESPACE_DNS, "medtech-internship-radar-catalog")`.
  It is **not** `f47ac10b-58cc-4372-a567-0e02b2c3d479`.

- Layered key (company is stripped and lowercased):

  1. If `req_id` is present → `company|req_id`
  2. Else if `row_kind` is `program_fallback` and `program_url` is present → `company|program_url`
  3. Else if apply URL is present → `company|canonical_url` (strip `utm_*` and session-looking query params; do not use raw Workday search URLs as identity)
  4. Else `company|normalized_title|normalized_location`

- Algorithm: `uuid.uuid5(CATALOG_NAMESPACE, key)`.
- Scrapers and seeds must not hardcode arbitrary IDs.

## Consequences

- Same posting always receives the same ID after refresh.
- ID changes require an explicit migration.
- Tests lock stability, `req_id` precedence, URL canonicalization, and the
  program-fallback key.
