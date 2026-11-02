# Current contributor state

Reconciled **2026-10-19**; publication status updated **2026-11-02**. [PLAN](../../PLAN.md) is the starting guide;
[verification evidence](../verification/2026-10-19-documentation.md) records what was checked.

## Approved scope

**32 device companies**, as recorded in `config/allowlist.json`: original 12 plus
approved waves 1 and 2. Default season: **summer-2027**. The original v1 T6.2 sign-off
on 2026-08-14 is historical. Further allowlist expansion requires a scope decision;
hospitals, pharma, Big Tech health, and website implementation remain outside scope.

## Implemented

Schema/IDs, generated role-family/newest/inactive views, issue merge, fallback seeds,
32 registered company scrapers, shared posting eligibility, daily archive transitions,
CI, and refresh via PR with dispatched CI and attempted squash merge are implemented.
Command, eligibility, and archive fixes are published on `main`, including refresh
publication hardening (`28b4448`) and qualification-scope fixes (`9f08281`). The
October 19 verification record retains its original tested base and dirty-state
limits; it does not describe the current publication status.

**Adapter implementation map (32/32):** Boston Scientific / Dexcom (Eightfold PCSX), Penumbra (Lever), Inspire Medical (Greenhouse), Abbott / Zimmer Biomet / GE HealthCare / STERIS / CONMED / Philips / Siemens Healthineers (Phenom `/widgets`), Intuitive (SmartRecruiters), CooperCompanies / Hologic (Oracle Recruiting CE), BD / Baxter (TalentBrew), Align (Pinpoint), Teleflex / Olympus / Arthrex (jobs2web search HTML), J&J MedTech (internships landing cards), Stryker (Paradox `/jobs?keyword=intern` preload JSON), Edwards (Algolia InstantSearch `EdwardsCareersJobs`), Integra LifeSciences (Kentico `/api/jobs/search` intern HTML), Medtronic / Insulet / Tandem / Smith+Nephew / ResMed / Globus Medical / Biotronik / Alcon (intern-hub JSON-LD JobPosting / intern job cards).

That map measures implementation, not live posting availability. The October 19
published snapshot contains 100 posting rows from 15 companies and 17 fallback hubs;
Medtronic is in the failed-scraper list. Stored rows can predate the current eligibility
gate. See [ELIGIBILITY](../ELIGIBILITY.md) for missing-evidence policy and cleanup.

## Remaining work

- Review existing current-season postings and submit a separate maintainer eligibility
  cleanup PR with source evidence, preserved identities, and generated views.
- Investigate recorded source failures and periodically verify live Apply/source
  behavior. An adapter test, a fallback link, and a green CI run prove different things.
- Inspect workflow failures independently of successful refreshes; the dated record
  includes both a successful dispatched CI run and a failed PR-event run without jobs.
- No additional adapter is required solely to reach implementation coverage. Retain
  fallback hubs when supported sources expose no eligible reqs.

Do not reverse-engineer Workday CXS/search, scrape Biotronik staging jobs2web,
university Handshake mirrors, or third-party aggregators. SuccessFactors
Biotronik/MSEI portals remain recorded as `loginFlowRequired` in source research.

## Historical source observations

These are August observations, not October live verification:

- [J&J](SLICE-JNJ.md), [Stryker](SLICE-STRYKER.md), and [Edwards](SLICE-EDWARDS.md):
  2026-08-15/16 intern-keyword results were non-US or non-STEM.
- [Integra](SLICE-INTEGRA.md): intern-keyword search empty on 2026-08-16.
- [Remaining hubs](SLICE-HUB-LANDING.md): program copy and Workday/SuccessFactors
  links, no intern job cards on 2026-08-17; Medtronic returned an Incorrect Browser wall.

The PM slice files preserve their original acceptance/source snapshots, including
statements that production was unchanged at that time. They are not a live backlog
or a current production report. Current health is in `data/health.json`.
