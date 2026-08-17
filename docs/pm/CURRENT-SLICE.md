# Loop state

**v1:** T6.2 signed off (locked 12 + archive/refresh).  
**Wave 1 / 2:** allowlist signed off — 32 device companies.  
**Adapters (32/32):** Boston Scientific / Dexcom (Eightfold PCSX), Penumbra (Lever), Inspire Medical (Greenhouse), Abbott / Zimmer Biomet / GE HealthCare / STERIS / CONMED / Philips / Siemens Healthineers (Phenom `/widgets`), Intuitive (SmartRecruiters), CooperCompanies / Hologic (Oracle Recruiting CE), BD / Baxter (TalentBrew), Align (Pinpoint), Teleflex / Olympus / Arthrex (jobs2web search HTML), J&J MedTech (internships landing cards), Stryker (Paradox `/jobs?keyword=intern` preload JSON), Edwards (Algolia InstantSearch `EdwardsCareersJobs`), Integra LifeSciences (Kentico `/api/jobs/search` intern HTML), Medtronic / Insulet / Tandem / Smith+Nephew / ResMed / Globus Medical / Biotronik / Alcon (intern-hub JSON-LD JobPosting / intern job cards). Live J&J intern cards, Stryker intern-keyword hits, and Edwards intern-keyword hits on 2026-08-15/16 were non-US (or non-STEM). Integra intern keyword search was empty on 2026-08-16. Remaining intern hubs on 2026-08-17 still have program copy plus Workday/SuccessFactors apply links, not intern job cards. Medtronic early-careers still returns an Incorrect Browser wall to the catalog user-agent. Production catalog is unchanged until daily refresh.

**Next:** none for adapter coverage. Do **not** reverse-engineer Workday CXS/search. Do not scrape Biotronik staging jobs2web, university Handshake mirrors, or third-party aggregators. SuccessFactors Biotronik/MSEI portals stay `loginFlowRequired`.

**Stop expanding the allowlist** unless new researched **device** intern hubs appear. Do not add hospitals, pharma, or Big Tech health.
