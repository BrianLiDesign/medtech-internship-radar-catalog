# Slice — Dexcom Eightfold + Align Pinpoint

**Status:** Implemented with mocked tests. Boston Scientific PCSX logic now lives in `scripts/eightfold_adapter.py` (BSC behavior unchanged). Align uses public Pinpoint `jobs.json`. Production catalog is unchanged until daily refresh.

**Locked constraints:** Public JSON only. Do not reverse-engineer Workday CXS/search. Mock HTTP in CI.

## Scope

| Company | Endpoint |
|---------|----------|
| Dexcom | `GET https://careers.dexcom.com/api/pcsx/search?domain=dexcom.com&query=intern` |
| Align | `GET https://jobs.aligntech.com/jobs.json` |

Live Dexcom intern-keyword PCSX includes titles such as Facilities Engineer Intern. Live Align intern-titled rows on 2026-08-15 were Costa Rica / Poland (inclusion drops).

## Behaviors to test

1. Framework still registers `Boston Scientific`; also registers `Dexcom` and `Align`.
2. Dexcom fixture (shared PCSX JSON) keeps US STEM intern titles and drops HR.
3. Align fixture keeps US STEM intern; drops Costa Rica intern, Poland intern, HR intern, and “International” FT titles.
4. Empty Pinpoint `data` keeps the hub. 403 soft-fails.
