# Slice — remaining intern-hub landing adapters

**Status:** Implemented with mocked tests. Live intern hubs on 2026-08-17 have program copy and Workday/SuccessFactors apply links, not intern job cards or JobPosting JSON-LD. Production catalog stays on program-fallback until a hub grows real intern req links. Medtronic early-careers still returns an Incorrect Browser wall to the catalog user-agent.

**Locked constraints:** Public intern-hub HTML only (JSON-LD `JobPosting` and intern-titled `/job/` cards). Do not reverse-engineer Workday CXS/search. Do not follow staging jobs2web (`valhalla` / `stage.`). Do not scrape university Handshake mirrors or third-party aggregators. Individual Workday **job** apply URLs with req ids are allowed as `apply_url`. Mock HTTP in CI.

## Scope

| Company | Source |
|---------|--------|
| Medtronic | `https://www.medtronic.com/en-us/our-company/careers/early-careers.html` |
| Insulet | `https://www.insulet.com/working-at-insulet/students-and-early-careers` |
| Tandem | `https://www.tandemdiabetes.com/about-us/careers/internship-program` |
| Smith+Nephew | `https://www.smith-nephew.com/en-us/careers` |
| ResMed | `https://careers.resmed.com/careers/early-careers/` |
| Globus Medical | `https://www.globusmedical.com/about/careers/` |
| Biotronik | `https://www.biotronik.com/en-us/careers/career-levels/students` |
| Alcon | `https://www.alcon.com/careers/early-careers/` |

Adapter: `scripts/hub_landing_adapter.py` plus `config/scrapers/<company>_scraper.py`.

## Behaviors to test

1. Framework registers all eight remaining allowlist names.
2. Fixture US STEM intern is a `posting`; HR, sales, non-US, alumni `/people/`, and staging jobs2web URLs drop.
3. Empty hub HTML keeps the program-fallback hub.
4. 403 soft-fail.
5. Medtronic Incorrect Browser wall soft-fail.
