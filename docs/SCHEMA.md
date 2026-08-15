# Internship catalog schema

Internship-native JSON Schema for one catalog row. Catalog files
(`data/active/internships.json` and `data/archived/internships.json`) are
**arrays** of these objects. Empty arrays are valid.

Schema file: [`data/schema.json`](../data/schema.json) (JSON Schema draft-07).
Validate with `python scripts/validate_data.py` (or `make validate`).

Example rows (one `posting` and one `program_fallback`):
[`tests/fixtures/example_internships.json`](../tests/fixtures/example_internships.json).

## Required fields

| Field | Meaning |
|-------|---------|
| `id` | UUID v5 from `scripts/internship_ids.py` |
| `company` | Employer name |
| `title` | Posting title, or program name for a fallback row |
| `apply_url` | Direct apply URL (or internship-program URL for fallback). Required; rows without it are omitted from the README later |
| `season` | `summer-YYYY` (v1 default `summer-2027`; later summers allowed) |
| `role_family` | README grouping enum |
| `location` | US city/state list, or `Remote (US)`. Join sites with `; ` when one apply URL covers many cities |
| `degree` | `bs` \| `ms` \| `bs_ms` \| `unspecified` (README later shows unspecified as `BS/MS`) |
| `row_kind` | `posting` or `program_fallback` |
| `source` | `scrape` \| `seed` \| `issue` |
| `first_seen` | Date the catalog first recorded the row (`YYYY-MM-DD`) |
| `last_seen` | Liveness date (`YYYY-MM-DD`). Not used for Age |

## Enums

**`row_kind`:** `posting` | `program_fallback`

**`role_family`:** Software; BME/R&D; Electrical/firmware; Mechanical/robotics; Data/ML; Quality/manufacturing; Other STEM

**`degree`:** `bs` | `ms` | `bs_ms` | `unspecified`

**`source`:** `scrape` | `seed` | `issue`

**`season`:** pattern `summer-[0-9]{4}` so `summer-2027` and later summers validate.

## Optional fields

| Field | Meaning |
|-------|---------|
| `req_id` | Employer requisition ID (wins identity over URL) |
| `posted_at` | Employer posted date; Age prefers this over `first_seen` |
| `work_auth` | `citizen_only` \| `us_auth_no_sponsor` \| `unspecified` (stored, not a v1 filter) |
| `eligibility` | `open` \| `returning` |
| `closed_at` | Date archived |
| `close_reason` | Why the row left the active catalog |
| `miss_count` | Consecutive daily misses |
| `canonical_apply_url` | Apply URL after tracking-param strip |
| `program_url` | Internship portal URL; identity key for `program_fallback` |
| `ats` | Suspected ATS name |
| `short_description` | Brief posting/program blurb |

## Identity

See [ADR 0002](adr/0002-internship-ids-uuid-v5.md). Duplicate `id` values fail validation.

## What this schema is not

This is not a campus-program schema. It has no `role_type`, `domain`,
ambassador fields, or a 60-day freshness SLO. Intern rows go stale in days;
close/archive rules live in `scripts/archive_closed.py` (ATS-closed, two consecutive posting misses, two program-URL deaths, or force-close).
