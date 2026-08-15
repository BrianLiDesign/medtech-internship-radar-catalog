"""Generated README dashboard (fixtures only; no live network)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from generate_dashboard import generate_readme, load_current_season


def internship(**overrides):
    row = {
        "id": "11111111-1111-4111-8111-111111111111",
        "company": "Medtronic",
        "title": "Software Intern",
        "apply_url": "https://jobs.example.com/software-intern",
        "season": "summer-2027",
        "role_family": "Software",
        "location": "Minneapolis, MN",
        "degree": "unspecified",
        "row_kind": "posting",
        "source": "seed",
        "first_seen": "2026-08-11",
        "last_seen": "2026-08-14",
    }
    row.update(overrides)
    return row


NOW = date(2026, 8, 14)


def test_unspecified_degree_renders_as_bs_ms():
    readme = generate_readme(
        [internship(degree="unspecified")],
        season="summer-2027",
        now=NOW,
    )
    assert "| BS/MS |" in readme
    assert "| unspecified |" not in readme


def test_age_uses_posted_at_when_set_else_first_seen():
    posted = internship(
        company="Abbott",
        title="Posted Intern",
        posted_at="2026-08-11",
        first_seen="2026-07-01",
        role_family="Software",
    )
    first_seen_only = internship(
        id="22222222-2222-4222-8222-222222222222",
        company="Dexcom",
        title="Seen Intern",
        first_seen="2026-07-15",
        role_family="Software",
    )
    readme = generate_readme([posted, first_seen_only], season="summer-2027", now=NOW)
    abbott = next(line for line in readme.splitlines() if "| Abbott |" in line)
    dexcom = next(line for line in readme.splitlines() if "| Dexcom |" in line)
    assert abbott.endswith("| 3d |")
    assert dexcom.endswith("| 1mo |")


def test_program_fallback_age_is_em_dash_without_posted_at():
    hub = internship(
        company="Medtronic",
        title="University internships",
        row_kind="program_fallback",
        role_family="Other STEM",
        first_seen="2026-08-14",
        last_seen="2026-08-14",
    )
    dated_hub = internship(
        id="22222222-2222-4222-8222-222222222222",
        company="Abbott",
        title="University Internship Program",
        row_kind="program_fallback",
        role_family="Other STEM",
        posted_at="2026-08-11",
        first_seen="2026-08-14",
    )
    readme = generate_readme([hub, dated_hub], season="summer-2027", now=NOW)
    medtronic = next(line for line in readme.splitlines() if "| Medtronic |" in line)
    abbott = next(line for line in readme.splitlines() if "| Abbott |" in line)
    assert medtronic.endswith("| — |")
    assert abbott.endswith("| 3d |")


def test_row_without_apply_url_is_omitted():
    listed = internship(company="Medtronic", title="Has Apply")
    omitted = internship(
        id="33333333-3333-4333-8333-333333333333",
        company="Intuitive",
        title="No Apply",
        apply_url="",
    )
    missing_key = internship(
        id="44444444-4444-4444-8444-444444444444",
        company="Stryker",
        title="Missing Apply",
    )
    del missing_key["apply_url"]
    readme = generate_readme(
        [listed, omitted, missing_key],
        season="summer-2027",
        now=NOW,
    )
    assert "Has Apply" in readme
    assert "No Apply" not in readme
    assert "Missing Apply" not in readme
    assert "Intuitive" not in readme
    assert "Stryker" not in readme


def test_empty_role_families_omitted_and_season_comes_from_config(tmp_path):
    season_path = tmp_path / "current_season.json"
    season_path.write_text('{"season": "summer-2027"}\n', encoding="utf-8")
    season = load_current_season(season_path)
    assert season == "summer-2027"
    rows = [
        internship(role_family="Software", season="summer-2027"),
        internship(
            id="55555555-5555-4555-8555-555555555555",
            company="GE HealthCare",
            title="ML Intern",
            role_family="Data/ML",
            season="summer-2028",
        ),
    ]
    readme = generate_readme(rows, season=season, now=NOW)
    assert "## Software" in readme
    assert "Software Intern" in readme
    assert "## Data/ML" not in readme
    assert "ML Intern" not in readme
    assert "## BME/R&D" not in readme
    assert "## Electrical/firmware" not in readme
    assert "## Mechanical/robotics" not in readme
    assert "## Quality/manufacturing" not in readme
    assert "## Other STEM" not in readme


def test_apply_cell_uses_in_repo_badge():
    url = "https://jobs.example.com/software-intern"
    readme = generate_readme([internship(apply_url=url)], season="summer-2027", now=NOW)
    assert f"[![Apply](assets/apply.svg)]({url})" in readme
    assert "https://img.shields.io" not in readme


TWELVE_FALLBACKS = Path(__file__).resolve().parent / "fixtures" / "dashboard_twelve_fallbacks.json"

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


def test_twelve_fallback_fixture_renders_all_company_names():
    rows = json.loads(TWELVE_FALLBACKS.read_text(encoding="utf-8"))
    readme = generate_readme(rows, season="summer-2027", now=NOW)
    missing = [name for name in V1_COMPANIES if name not in readme]
    assert missing == []
    assert all(row["row_kind"] == "program_fallback" for row in rows)
    assert all("example.com" in row["apply_url"] for row in rows)


def test_role_family_jump_links_show_counts_before_tables():
    rows = [
        internship(role_family="Software", company="Medtronic", title="Software Intern"),
        internship(
            id="66666666-6666-4666-8666-666666666666",
            company="Abbott",
            title="Second Software Intern",
            role_family="Software",
        ),
        internship(
            id="77777777-7777-4777-8777-777777777777",
            company="Dexcom",
            title="BME Intern",
            role_family="BME/R&D",
        ),
    ]
    readme = generate_readme(rows, season="summer-2027", now=NOW)
    preamble = readme[: readme.index("## Software")]
    assert "[Software](#software) (2)" in preamble
    assert "[BME/R&D](#bmerd) (1)" in preamble
    assert "Electrical/firmware" not in preamble
    assert "Data/ML" not in preamble


def test_empty_catalog_keeps_discover_first_structure():
    readme = generate_readme([], season="summer-2027", now=NOW)
    assert readme.startswith("# MedTech Internship Radar Catalog")
    assert "Summer 2027" in readme
    assert "No listings yet" in readme
    assert "## Software" not in readme
    assert "## Other STEM" not in readme
    assert "Student Program Radar" not in readme
    assert "student-program-radar" not in readme
    assert "| Visa |" not in readme
    assert "CC-BY 4.0" in readme
    assert "[MIT](LICENSE.md)" in readme
    assert "[CONTRIBUTING.md](CONTRIBUTING.md)" in readme
    assert "[SECURITY.md](SECURITY.md)" in readme
