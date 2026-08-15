"""Public contribution docs stay internship-native and off the listings JSON."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

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

PUBLIC_DOCS = (
    REPO_ROOT / "CONTRIBUTING.md",
    REPO_ROOT / "SECURITY.md",
    REPO_ROOT / "docs" / "DEVELOPMENT.md",
    REPO_ROOT / "docs" / "SCRAPER_CHECKLIST.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "add-internship.yml",
    REPO_ROOT / ".github" / "pull_request_template.md",
)

FORBIDDEN = ("Student Program Radar", "student-program-radar")


def test_add_internship_template_dropdown_is_the_allowlist():
    text = (REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "add-internship.yml").read_text(
        encoding="utf-8"
    )
    assert "id: company" in text
    assert "type: dropdown" in text
    for name in ALLOWLIST_COMPANIES:
        assert f"- {name}" in text, name
    company_block = text.split("id: company", 1)[1]
    options_block = company_block.split("options:", 1)[1].split("validations:", 1)[0]
    listed = [
        line.strip()[2:] for line in options_block.splitlines() if line.strip().startswith("- ")
    ]
    assert listed == list(ALLOWLIST_COMPANIES)


def test_public_docs_do_not_mention_the_other_radar_product():
    for path in PUBLIC_DOCS:
        text = path.read_text(encoding="utf-8")
        for phrase in FORBIDDEN:
            assert phrase not in text, f"{path.name} contains {phrase!r}"


def test_contributing_says_listings_json_is_maintainer_owned():
    text = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "data/active/internships.json" in text
    assert "automation" in text.lower()
    assert "maintainer" in text.lower()
    assert "must not" in text.lower() or "do not" in text.lower()
    assert "candidates" in text.lower()
    assert "allowlist" in text.lower()
    assert "merge_issue.py" in text
    assert "source: issue" in text


def test_security_md_points_at_private_advisories():
    text = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "private" in text.lower()
    assert "advisories" in text.lower() or "advisory" in text.lower()
    assert "public issue" in text.lower()


def test_scraper_checklist_is_internship_native_and_mocked():
    text = (REPO_ROOT / "docs" / "SCRAPER_CHECKLIST.md").read_text(encoding="utf-8")
    assert "InternshipScraper" in text
    assert "mocked HTTP" in text.lower() or "mocked HTTP" in text
    assert "Workday" in text
    assert "find_posting_urls" in text
    assert "parse_posting" in text
    assert "internships.json" in text
    assert "programs.json" not in text
    assert "EnhancedBaseScraper" not in text
