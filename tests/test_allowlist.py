"""Allowlist (v1 locked twelve + post-v1 waves) and parked candidates."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = REPO_ROOT / "config" / "allowlist.json"
CANDIDATES_PATH = REPO_ROOT / "config" / "candidates.json"

V1_COMPANIES = (
    "Medtronic",
    "Intuitive",
    "Abbott",
    "Dexcom",
    "Insulet",
    "Tandem",
    "Stryker",
    "Boston Scientific",
    "Edwards",
    "BD",
    "Zimmer Biomet",
    "GE HealthCare",
)

WAVE1_COMPANIES = (
    "J&J MedTech",
    "Siemens Healthineers",
    "Philips",
    "Penumbra",
    "Align",
)

WAVE2_COMPANIES = (
    "Smith+Nephew",
    "Baxter",
    "ResMed",
    "Hologic",
    "Teleflex",
    "Integra LifeSciences",
    "Globus Medical",
    "Arthrex",
    "STERIS",
    "CONMED",
    "Olympus",
    "CooperCompanies",
    "Biotronik",
    "Alcon",
    "Inspire Medical",
)

ALLOWLIST_COMPANIES = V1_COMPANIES + WAVE1_COMPANIES + WAVE2_COMPANIES

ALLOWED_ATS = {"workday", "greenhouse", "lever", "eightfold", "unknown"}


def test_allowlist_has_v1_plus_wave_companies_with_public_hub_urls_and_ats_notes():
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    companies = payload["companies"]
    names = [company["name"] for company in companies]
    assert names == list(ALLOWLIST_COMPANIES)
    assert len(companies) == 32
    assert names[:12] == list(V1_COMPANIES)
    assert names[12:17] == list(WAVE1_COMPANIES)
    assert names[17:] == list(WAVE2_COMPANIES)
    for company in companies:
        assert company["hub_url"].startswith("https://"), company["name"]
        assert company["ats"] in ALLOWED_ATS, company["name"]
        assert company["notes"].strip(), company["name"]


def test_candidates_are_empty_after_wave2_and_promoted_names_stay_on_allowlist():
    payload = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    names = [candidate["name"] for candidate in payload["candidates"]]
    assert names == []
    for promoted in WAVE1_COMPANIES + WAVE2_COMPANIES:
        assert promoted not in names, promoted
    allowlist_names = {
        company["name"]
        for company in json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))["companies"]
    }
    assert allowlist_names.isdisjoint(names)
    assert set(WAVE1_COMPANIES) <= allowlist_names
    assert set(WAVE2_COMPANIES) <= allowlist_names
    assert set(V1_COMPANIES) <= allowlist_names
