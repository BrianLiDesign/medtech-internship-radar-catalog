# Independent eligibility acceptance expectations

Historical October 28 bounded acceptance record. A subsequent read-only review
found six additional defects; their November 1 remediation and renewed acceptance
are tracked in [the revision record](2026-11-01-revision-plan.md). The earlier
verdict below does not certify those later findings as resolved.

Established 2026-10-28 from the user requirements, existing eligibility policy,
and reported regression cases, before inspecting the redesign implementation.
These expectations are separate from the implementation's own test assertions.
All examples assume an otherwise qualifying US software/research internship for
Summer 2027. Missing degree evidence remains accepted under existing policy.

## Decision contract

`accept` permits ingestion; `reject` is an affirmative policy exclusion; `review`
means qualification evidence exists but its meaning or scope cannot be established.
Review cases must be withheld from confirmed eligibility and expose their source
field and source clause. Review is distinct from a failed scraper and from proof
that the employer closed a posting.

| Qualification evidence | Expected | Independent reason |
|---|---|---|
| No degree evidence | accept | Preserve missing-evidence policy. |
| `Must be pursuing a PhD in computer science.` | reject | Mandatory doctoral enrollment excludes the BS/MS audience. |
| `Currently enrolled in a doctoral program.` | reject | Enrollment qualification is mandatory absent preference language. |
| `Requirements: Ph.D. in engineering.` | reject | Qualification heading supplies mandatory scope. |
| `Education: PhD in engineering.` | reject | Explicit education evidence identifies a doctoral audience. |
| `PhD preferred.` | accept | A preference is not a bar. |
| `Candidates pursuing a PhD preferred.` | accept | Enrollment language does not override an explicit local preference. |
| `PhD preferred; Python required.` | accept | Skill requirement cannot promote degree preference into a requirement. |
| `Python required and PhD preferred.` | accept | Same qualifications and modalities in reverse order. |
| `PhD preferred with MS Office required.` | accept | Microsoft skill requirement is unrelated to the credential. |
| `PhD required; Python preferred.` | reject | Skill preference cannot weaken mandatory degree. |
| `Currently enrolled in a PhD program with Python experience preferred.` | reject | Enrollment and skill have separate scopes. |
| `Must have a PhD and proficiency in MS Office.` | reject | MS Office is not an alternative master's credential. |
| `Must have a PhD and proficiency in Microsoft Office.` | reject | Equivalent to abbreviated product name. |
| `BS completed. Must be enrolled in a PhD program.` | reject | Prior education does not create an eligibility alternative. |
| Separate fields: `degreeRequirements: PhD`, `education: Bachelor degree completed.` | reject | Independent degree field cannot cancel a doctoral requirement. |
| `Pursuing a BS, MS, or PhD in engineering.` | accept | Explicit shared alternative requirement. |
| `Pursuing a BS/MS/PhD in engineering.` | accept | Slash audience list is an established alternative form. |
| Structured `educationRequirements: [BS, MS, PhD]` | accept | An enumerated credential audience is an explicit alternative list. |
| `Bachelor's or PhD` in supplied degree field | accept | Explicit alternative relation. |
| `Work with PhD scientists on software.` | accept | Colleague credential is not applicant qualification. |
| Bare `PhD and MS` without further relation | review | It could mean cumulative credentials or imprecise audience shorthand. |
| `PhD may be required depending on project.` | review | Conditional doctoral restriction cannot establish BS/MS eligibility. |
| `PhD required or preferred.` | review | Conflicting local modality is unresolved. |

## Invariants

1. Adding unrelated skill requirements does not alter degree eligibility.
2. Adding unrelated preferences does not weaken mandatory qualifications.
3. `MS Office` and `Microsoft Office` produce identical outcomes.
4. Genuine BS/MS/PhD alternatives stay accepted; proximity alone never establishes
   an alternative. A historical degree or a skill containing MS is insufficient.
5. Reordering independent fields or clauses does not alter the outcome.
6. Equivalent HTML paragraphs/list items and plain-text clauses preserve decisions.
   Ordinary formatting tags must not merge modalities across qualifications.
7. Every parsed qualification retains credential/skill, modality, and source clause.
   Ambiguous degree evidence is visible as review rather than accepted silently.
8. A mandatory independent doctoral qualification dominates unrelated accepted or
   preferred qualifications; one alternative list does not erase another requirement.

## Ingestion and refresh acceptance

Run the contract cases through all ten existing JSON/preload/JSON-LD adapter routes
and full temporary refreshes. Mock HTTP; do not write fixtures into production.
Accepted rows preserve stable UUID identity and first-seen dates across refreshes.
Rejected/review candidates are absent from newly ingested active postings. Existing
rows follow documented archive semantics; withholding a review row is not an
immediate ATS-closure signal. Verify adjacent-date miss rules, archive uniqueness,
rediscovery, and preservation of existing identities. A blocked company must not
prevent valid rows from other companies from being ingested and must preserve its
posting miss state unless definitive closure evidence exists. Review artifacts
must not report the company as blocked merely because a qualification is unclear.

## Review status

Independent expectations established before implementation inspection. The first
implementation audit ran direct `classify_posting` calls with new adversarial
variants and found the following defects. Implementation acceptance is pending
remediation and recheck; the passing implementation tests alone are insufficient.

| Finding | Observed input and outcome | Expected / violated criterion |
|---|---|---|
| P2 alternative grammar | `Must have a BS degree or a PhD degree.` -> reject; `Pursuing a BS, an MS, or a PhD in engineering.` -> reject | accept; genuine alternatives are not limited to adjacent bare abbreviations |
| P2 governing modality and referents | `Must have Python proficiency and a PhD.` -> review; `PhD preferred, but required for some projects.` -> accept | reject / review; retain governing requirement and unresolved conditional referent |
| P2 section structure parity | structured `lists: [{text: Preferred Qualifications, content: PhD}]` -> reject, plain `Preferred Qualifications\nPhD` -> accept | both accept; section capitalization and representation cannot alter meaning |
| P2 inline section continuity | under `description.qualifications`, `Preferred qualifications: Python\nPhD` -> reject, `Preferred qualifications\nPython\nPhD` -> accept | both accept; inline heading governs its subsequent section lines |
| P2 qualification subject | `Experience collaborating with PhD scientists required.` -> reject | accept; required experience with credentialed colleagues is not applicant doctoral education |
| P2 contradictory modality | `Must be pursuing a PhD preferred.` -> accept | review; enrollment vocabulary must not hide an explicit must/preferred contradiction |
| Optional wording gap | `PhD is optional.` -> review, `PhD not required.` -> accept | both accept; explicit optional wording is not ambiguous |

These checks used transient local Python invocations with no live HTTP and did not
modify catalog data or implementation tests.

### Remediation recheck

All original reported examples now produce the expected decision, including
`and/or` alternatives, capitalized structured preference sections, inline heading
continuity, explicit optional text, and the original colleague-only example.
An independent run of the contract, adapter, and temporary refresh suites passed:
`603 passed in 29.32s`. The refresh tests exercise all ten adapter routes for every
decision case, then repeat refreshes to verify identities and first-seen dates.
The lifecycle test distinguishes blocked scrapers, withheld decisions, ordinary
discovery misses, archive uniqueness, and rediscovery.

Further adversarial recheck found three remaining scope/representation gaps:

| Input | Observed | Expected |
|---|---|---|
| `Must have a PhD and work with PhD scientists.` | accept | reject; colleague mention must not override a separate mandatory applicant credential |
| `Candidates must have Python proficiency and a PhD.` | review | reject; an applicant subject before `must` preserves governing modality |
| `ph.D. required. Python preferred.` | review | reject; dotted credential capitalization cannot change sentence semantics |

Acceptance remains pending resolution and final recheck of these gaps. The review
sidecar is local source evidence beside the failure artifact and is separate from
sanitized refresh diagnostics and scraper-blocked status.

### Final bounded recheck

The three subsequent scope/representation gaps above are remediated: all their
reported inputs now produce expected outcomes. The final contract, adapter, and
temporary refresh suites passed independently: `655 passed in 33.75s`. An
additional 96 combinations, constructed independently of those test expectations,
passed for required/preferred degree text combined with Java, communication, MS
Office, and Microsoft Office skills in both orders across six separators.

The review queue preserves stable posting identity, source clauses, sweep date,
and target season; each completed scrape rewrites it separately from the blocked
scraper artifact. Review withholding follows ordinary adjacent-date discovery
miss semantics for existing rows, while blocked companies preserve miss state.
The tests and code confirm that clarification can rediscover the original ID and
first-seen date. Raw source evidence stays in a local sidecar; the workflow's
failure-diagnostics upload glob does not include it.

One final supported-representation defect remains pending: `Ph. D. required.
Python preferred.` currently accepts, while `Ph.D. required. Python preferred.`
rejects. The credential pattern recognizes the spaced spelling but sentence
splitting loses it at the internal period. Acceptance is conditional on resolving
this parity defect and rerunning its targeted check.

This review provides local deterministic and mocked-ingestion evidence. It does
not certify live source completeness, detail pages not requested by adapters, or
error-free interpretation of arbitrary job-description prose. No production
catalog writes, live HTTP, or deployment checks were performed by this reviewer.

### Acceptance verdict

**Accepted for the documented bounded contract on 2026-10-28.** All findings above
are resolved. The final spaced/dotted credential recheck passed for 16 spelling
and modality combinations, preserving the normalized source clause. A further
144 independently constructed skill/order/separator combinations passed,
including subjectful `Required Java skills` and `Communication skills required`.
The documented and executable contract both contain the same 36 case IDs.

Final independent focused gate:

```text
python -m pytest tests/test_qualification_contract.py tests/test_ingestion_eligibility.py tests/test_qualification_refresh.py -q
704 passed in 47.56s
```

Reviewed against the dirty working tree based on commit
`28b44483eb06db5b9dc6ebe6e089188f2ea55c39`. This verdict concerns the classifier
contract and mocked ingestion/refresh acceptance. The primary agent remains
responsible for the final repository-wide lint, format, test, and validation gate.
The local-only and arbitrary-prose limitations stated above continue to apply.
