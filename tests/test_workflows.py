"""GitHub Actions: daily refresh opens a PR; CI stays mocked-HTTP."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DAILY = REPO_ROOT / ".github" / "workflows" / "daily-catalog-refresh.yml"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_daily_workflow_opens_pr_and_never_pushes_listings_to_main():
    text = DAILY.read_text(encoding="utf-8")
    assert "scrape_internships.py" in text or "refresh_catalog.py" in text
    assert "validate_data.py" in text or "refresh_catalog.py" in text
    assert "archive_closed.py" in text or "refresh_catalog.py" in text
    assert "generate_dashboard.py" in text or "refresh_catalog.py" in text
    assert "automation/daily-catalog-refresh" in text
    assert "gh pr create" in text
    assert "git push origin main" not in text
    assert "HEAD:main" not in text
    assert "HEAD:master" not in text


def test_ci_runs_pytest_and_validate_without_live_scrape():
    text = CI.read_text(encoding="utf-8")
    assert "pytest" in text
    assert "validate_data.py" in text
    assert "scrape_internships.py" not in text
    assert "refresh_catalog.py" not in text or "--fixture" in text


def test_automation_doc_describes_local_dry_run_and_refresh_via_pr():
    text = (REPO_ROOT / "docs" / "AUTOMATION.md").read_text(encoding="utf-8")
    assert "refresh_catalog.py" in text
    assert "--fixture" in text
    assert "automation/daily-catalog-refresh" in text
    assert "main" in text.lower()
    assert "Student Program Radar" not in text
