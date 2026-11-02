# Automated posting eligibility

`scripts/inclusion.py` owns the shared decision; `scripts/qualifications.py`
preserves qualification scope. `scripts/posting_context.py` separates placement
terms from graduation dates and authorization phrases from role evidence. The reviewed [decision contract](QUALIFICATION-CONTRACT.md)
and its independent acceptance record define examples and invariants.
`InternshipScraper.scrape`
checks every parsed posting before creating a catalog row. Listing-cache
adapters retain candidates until this check, so an explicit ingestion season
cannot be overridden by an earlier check against the default season.
The default target comes from `config/current_season.json`; refresh passes its
`season_path` through ingestion as well as README generation. A parsed posting's
`season` is source evidence, not the requested target. Accepted rows receive the
target season. Program fallback seeds remain a separate, maintainer-managed path.

## Rules and missing evidence

| Evidence | Decision |
|---|---|
| Location | Must positively identify the US or US remote using the shared geography classifier. Missing location or unqualified `Remote` fails. |
| Internship | Title must identify an intern/internship or co-op. New-grad full-time titles fail. |
| STEM | Require a STEM marker in title, description, department/category, or education requirements. Engineering, software, science/research, data/analytics, regulatory, quality, manufacturing, and clinical roles qualify. Generic `Intern`, `Analyst Intern`, and `Undergraduate or Graduate Intern` fail without supporting STEM evidence. The uppercase `IT` abbreviation qualifies in a role title or an exact department/category value; ordinary prose needs explicit wording such as `information technology`, so the pronoun `it` is not evidence. |
| Non-STEM | Finance/financial/accounting, brand management, people services/operations, HR, marketing, sales, business, recruiting, communications, and legal titles fail even when company boilerplate mentions engineering. Business intelligence/analytics/systems are explicit STEM exceptions. For ambiguous titles, supporting evidence must contain STEM and no explicit non-STEM marker. |
| Season | Missing year/term is allowed for internships. An explicit year in the title or source term must match the target year. A named summer/year in description/category must match; explicit fall/spring/winter terms (including `internship is in` and `internship is for` wording), rotating, and multi-term co-ops fail. Graduation-linked seasons/years are ignored; graduate-student audiences do not establish graduation context. Separate placement terms remain binding. A co-op additionally needs affirmative summer evidence. |
| Degree | Missing/unspecified is allowed. Required doctoral-only qualifications reject. Local preferences, optional degrees, and colleague credentials do not exclude. Explicit BS/MS/PhD alternatives qualify; nearby degrees alone are insufficient. Prior BS education and unrelated skill preferences never cancel a required PhD. MS Office is a skill. Unresolved credential relations or conditional/conflicting doctoral requirements produce `review`. |
| Work authorization | Never an exclusion criterion. Existing work-auth and returning/internal tags remain descriptive only. |

The classifier exposes `accept`, `reject`, and `review`, with qualification-level
modality, source path, clause, and explicit alternative evidence. The boolean
compatibility gate permits only `accept`. Ambiguous qualifications are withheld
from new ingestion and recorded in `ScrapeResult.reviews`. The runner writes
`logs/scrape_failures-qualification-reviews.json` (or a sibling named
`<artifact-stem>-qualification-reviews.json` for custom artifact paths), including
stable posting ID, sweep date, target season, and source evidence. It prints the
review count and evidence path. The file is rewritten each completed scrape sweep;
it is a local review queue, separate from scraper failures and sanitized diagnostics.
Raw source clauses are not uploaded by the failure-diagnostics workflow or committed
as catalog data. Maintainers inspect the source and clarify the contract before
broadening ambiguous syntax. Review evidence does not immediately archive stored rows.

These are deterministic text heuristics, not a semantic guarantee. Descriptions
can be incomplete or contain historical term references; conflicting term
evidence is rejected conservatively. Unclear roles need maintainer review and
representative tests before broadening the vocabulary. Do not infer STEM from
`role_family` (whose default is `Other STEM`), the company name, or degree level
alone. Do not infer a role's term from posting timestamps or graduation years.

## Adapter evidence trace

All adapters supply title, normalized location, and apply URL. The JSON adapters
also use `posting_evidence` to retain available description, education, and term
fields as transient evidence. No full description or raw requirements are added
to the catalog schema. Missing fields stay unknown; no additional detail-page
requests or Workday reverse engineering are introduced.

| Adapter | Existing title/location evidence | Additional available evidence passed to the gate |
|---|---|---|
| Eightfold | `name`, `locations` | `department` plus common description/education/term fields |
| Phenom | `title`, city/state/country fields | `category`/`type` plus common fields |
| Greenhouse | `title`, `location.name` | `content` when present, plus common fields |
| Lever | `text`, `categories.location`/`allLocations`, country/remote | team, `descriptionPlain`/`description`, `lists`, `additionalPlain`, plus common fields |
| SmartRecruiters | `name`, structured `location` | department, `jobAd` sections when present, plus common fields |
| Pinpoint | `title`, `location` | department, `description`, plus common fields |
| Oracle CE | `Title`, primary location/country | job family/department, `JobDescriptionStr`, `ExternalQualificationsStr`, plus common fields |
| Algolia | posting title, location/country | category/employee type, plus common fields |
| Stryker preload | `title`, structured locations | common fields when present |
| Hub JSON-LD | `title`, `jobLocation` | employment type, `description`, `educationRequirements`, plus common fields |
| Hub anchor cards | link title and associated location | No description/degree/term beyond title |
| TalentBrew, jobs2web, J&J cards | listing title/location | No description/degree/term beyond title |
| Kentico table | title/location | category; no description/degree/term beyond title |

The common fields are explicitly enumerated in `posting_evidence`: description
and qualification fields, degree/education fields, and `season`, `Season`, `term`,
or `internshipSeason`. Nested fields, labeled sections, and list boundaries are
retained for qualification parsing; HTML is normalized without execution. Only
text used for role/term checks and descriptive tags is flattened.
Search responses that omit descriptions or qualifications cannot establish a
PhD restriction hidden on an unrequested detail page. Mocked ingestion tests
cover all ten JSON/preload/JSON-LD routes, in addition to the existing HTML
adapter fixtures and classifier tests.

## Existing active rows: reviewed maintainer cleanup

Changing discovery does **not** delete existing rows: `upsert_catalog` retains
unseen IDs. Healthy scrapes normally age rejected rows out after two misses;
blocked scrapes preserve them. Neither is an immediate cleanup guarantee.

Use a **separate maintainer cleanup PR** after this classifier change lands:

1. Review active **posting** rows for the current ingestion season. Check title,
   location, and available source term/degree evidence against the rules above.
   Record a reviewed list of existing IDs, apply URLs, rejection reasons, and
   source evidence in the PR. Include known finance, brand management,
   people-services, Summer 2026, and confirmed PhD-only examples. Do not infer
   a missing PhD restriction from stored `degree: unspecified`; inspect the
   source when needed. Do not sweep program fallbacks or historical seasons.
2. Add a mocked regression case for any source evidence the adapters still lose
   before proceeding. This prevents the next refresh from reintroducing a row.
3. On the maintainer branch, use the existing force-close command, repeating
   `--force-close` for each reviewed ID:

   ```bash
   python -m scripts.validate_data
   python -m scripts.archive_closed --force-close <reviewed-id-1> --force-close <reviewed-id-2>
   python -c "from pathlib import Path; from scripts.apply_seeds import restore_missing_fallbacks; restore_missing_fallbacks(Path('data/active/internships.json'))"
   python -m scripts.validate_data
   python -m scripts.generate_dashboard
   ```

   `archive_closed` performs the regular archive sweep too. Review **all** data
   changes, including any ordinary miss-count updates, before submitting. It
   moves the original records into archived data with `close_reason: force_close`
   and `closed_at`; it preserves IDs, requisition IDs, URLs, and first-seen dates.
   The PR evidence distinguishes eligibility correction from actual ATS closure.
   `restore_missing_fallbacks` restores approved fallback coverage where necessary
   without rewriting existing fallbacks.
4. Verify each selected ID is absent from active data and present exactly once
   in archived data, with its original identity. Run `make lint test validate e2e`.
   Inspect regenerated active/inactive README views and submit the maintainer
   PR for review. No direct push to main and no contributor hand-edited data.

This implementation PR deliberately does not mutate active/archived catalogs or
regenerate published tables. The cleanup PR is an explicit follow-up, not an
assumed effect of merging the classifier.
