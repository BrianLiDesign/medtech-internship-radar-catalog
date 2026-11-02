# Qualification decision contract

Established 2026-10-28 from the hardening request. The independent
[acceptance review](verification/eligibility-independent-acceptance.md) establishes
expectations separately from implementation. This table's executable cases live in
[qualification_decisions.json](../tests/fixtures/qualification_decisions.json).
Examples use an otherwise qualifying US Software Intern for Summer 2027 unless
a case explicitly supplies another title. Text is description evidence. Revisions
on 2026-11-01 add the six review findings and independent counterexamples; see
[revision plan](verification/2026-11-01-revision-plan.md). Supplied education fields and title
credentials additionally identify an applicant audience by default; description
mentions without a local modality require review. No degree evidence remains allowed.

| Case | Title | Source qualification text | Outcome |
|---|---|---|---|
| unknown | Software Intern | (missing) | accept |
| doctoral-required | Software Intern | PhD required. | reject |
| enrollment | Software Intern | Currently enrolled in a PhD program. | reject |
| preferred-plus-required-skill | Software Intern | PhD preferred and Python required. | accept |
| required-plus-preferred-skill | Software Intern | PhD required and Python preferred. | reject |
| enrollment-with-preference | Software Intern | Currently enrolled in a PhD program with Python experience preferred. | reject |
| office-is-skill | Software Intern | PhD required with MS Office proficiency. | reject |
| microsoft-is-skill | Software Intern | PhD required with Microsoft Office proficiency. | reject |
| prior-bs | Software Intern | Bachelor's degree completed and must be pursuing a doctoral degree. | reject |
| slash-alternatives | Software Intern | Pursuing a BS/MS/PhD in engineering. | accept |
| or-alternatives | Software Intern | Pursuing a BS, MS, or PhD in engineering. | accept |
| bachelor-or-doctorate | Software Intern | Bachelor's or PhD required. | accept |
| colleagues | Software Intern | Work with PhD scientists on software. | accept |
| preferred | Software Intern | PhD preferred. | accept |
| ambiguous | Software Intern | PhD in engineering. | review |
| unlinked-degrees | Software Intern | PhD and MS. | review |
| cumulative-degrees | Software Intern | BS and PhD required. | reject |
| required-section | Software Intern | Required qualifications:<br>PhD in engineering.<br>Python experience. | reject |
| preferred-section | Software Intern | Preferred qualifications:<br>PhD in engineering.<br>Required qualifications:<br>Python experience. | accept |
| negation | Software Intern | PhD not required. | accept |
| negated-preference | Software Intern | PhD not preferred. | review |
| conditional | Software Intern | PhD required unless equivalent experience. | review |
| noun-alternatives | Software Intern | Must have a BS degree or a PhD degree. | accept |
| article-alternatives | Software Intern | Pursuing a BS, an MS, or a PhD in engineering. | accept |
| shared-must | Software Intern | Must have Python proficiency and a PhD. | reject |
| conditional-reference | Software Intern | PhD preferred, but required for some projects. | review |
| colleague-experience | Software Intern | Experience collaborating with PhD scientists required. | accept |
| conflicting-modality | Software Intern | Must be pursuing a PhD preferred. | review |
| optional | Software Intern | PhD is optional. | accept |
| conflicting-choice | Software Intern | PhD required or preferred. | review |
| conditional-project | Software Intern | PhD may be required depending on project. | review |
| required-with-colleagues | Software Intern | Must have a PhD and work with PhD scientists. | reject |
| required-with-colleague-preference | Software Intern | Must have a PhD, experience collaborating with PhD scientists preferred. | reject |
| subject-before-must | Software Intern | Candidates must have Python proficiency and a PhD. | reject |
| abbreviation-case | Software Intern | ph.D. required. Python preferred. | reject |
| abbreviation-space | Software Intern | Ph. D. required. Python preferred. | reject |
| applicant-purpose | Software Intern | Must have a PhD to work with our research team. | reject |
| applicant-purpose-colleagues | Software Intern | Must have a PhD to collaborate with PhD scientists. | reject |
| negated-optional | Software Intern | A PhD is not optional for this position. | reject |
| discipline-alternative | Software Intern | Must have a BS in engineering or a PhD in engineering. | accept |
| discipline-ms-alternative | Software Intern | Must be pursuing a PhD in Computer Science or a Master's degree in Engineering. | accept |
| required-h5 | Software Intern | <h5>Required qualifications: PhD</h5><h5>Preferred qualifications: Python</h5> | reject |
| graduation-season | Software Intern | Summer 2027 internship. Expected graduation: Spring 2028. | accept |
| graduation-and-placement | Software Intern | Graduating in Spring 2028; internship term: Summer 2026. | reject |
| graduation-heading | Software Intern | Expected graduation:<br>Spring 2028<br>Internship term: Summer 2027. | accept |
| same-clause-dates | Software Intern | Internship in Summer 2027 for students graduating in Spring 2028. | accept |
| legal-authorization-role | Intern | Develop software. Must have legal authorization to work in the United States. | accept |
| legal-role-control | Intern | Develop software for our legal department. | reject |
| finance-role-authorization | Intern | Finance work with data. Must have legal authorization to work in the United States. | reject |
| independent-doctoral-after-alternative | Software Intern | Must have a BS in engineering or a PhD in engineering. Must be enrolled in a PhD program. | reject |
| graduation-only-coop | Software Co-op | Expected graduation: Summer 2027. | reject |
| reversed-graduation-season | Software Intern | Internship term: Summer 2027. Expected graduation: 2028 Spring. | accept |
| graduate-student-placement | Software Intern | Internship for graduate students in Summer 2026. | reject |
| bare-placement-heading | Software Intern | Expected graduation:<br>Spring 2028<br>Internship term<br>Summer 2026 | reject |
| conjoined-discipline-alternative | Software Intern | Must have a BS in mathematics and statistics or a PhD in computer science. | accept |
| country-qualified-authorization | Intern | Develop software. Legal U.S. work authorization is required. | accept |

## Evidence and outcomes

Each qualification records its credential group or skill, local modality,
explicit alternative relation, source field path, normalized clause, and original
source clause. Headings apply within their source section; independent fields
never borrow each other's modality. A required doctoral qualification dominates
independent preferences and unrelated lower degrees. Only an explicit grammatical
alternative (or a structured enum of degree names) forms an alternative group.
Full sentences in education arrays are independent obligations, not alternatives.
Discipline modifiers can occur within explicit alternatives, including conjunctive
fields such as mathematics and statistics. Applicant credentials before a work-with
relation remain separate from colleague credentials after it. Negated optionality
is mandatory evidence. All six HTML heading levels retain section boundaries.

Placement evidence distinguishes graduation events from graduate-student audiences.
Graduation dates do not override placement dates, and a placement heading resets
previous graduation scope with or without a colon. Work-authorization noun phrases
are excluded from role evidence without removing real legal or finance roles.

`accept` permits ingestion; `reject` excludes a known out-of-scope candidate;
`review` withholds a candidate whose qualification meaning remains unresolved.
`include_posting` is a compatibility boolean and returns true only for `accept`.
Use `classify_posting` when inspecting evidence or uncertainty. Conditional or
conflicting doctoral qualifications are review cases. Supported preference,
optional, and colleague-credential statements do not exclude the candidate.

The grammar is bounded. It cannot guarantee correct interpretation of arbitrary
prose; unfamiliar syntax needs evidence review and a contract update before the
recognized grammar is broadened. Review does not assert that a job is closed.

## Required invariants and ingestion acceptance

- Unrelated skill requirements do not promote degree preferences to requirements.
- Unrelated preferences do not weaken mandatory degree requirements.
- MS Office and Microsoft Office are equivalent skills, never degree alternatives.
- Genuine BS/MS/PhD alternatives remain accepted; degree proximity is insufficient.
- Field order and equivalent HTML/plain-text block and inline formatting preserve decisions.
- The same decision cases traverse all ten JSON/preload/JSON-LD adapter routes,
  then staged refresh publication into temporary catalogs without live HTTP.
- Accepted rediscovery preserves stable identity and first_seen. Reject/review rows
  are withheld from new ingestion. Existing rows follow adjacent-date miss archive
  rules; rejected or ambiguous evidence is not treated as definitive ATS closure.
- Failed companies preserve miss state; other companies still ingest. Review
  evidence is distinct from blocked scraper failures and clears on a later sweep.

The tests observe public classifier decisions, `scrape`, and `refresh_catalog`.
Acceptance review must challenge this table and these invariants independently of
test results. A green test run alone is insufficient acceptance evidence.
