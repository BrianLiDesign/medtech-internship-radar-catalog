#!/usr/bin/env python3
"""Generate the student-facing README from the internship catalog."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

DEGREE_LABELS = {
    "bs": "BS",
    "ms": "MS",
    "bs_ms": "BS/MS",
    "unspecified": "BS/MS",
}

ROLE_FAMILIES = (
    "Software",
    "BME/R&D",
    "Electrical/firmware",
    "Mechanical/robotics",
    "Data/ML",
    "Quality/manufacturing",
    "Other STEM",
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ACTIVE = REPO_ROOT / "data" / "active" / "internships.json"
DEFAULT_ARCHIVED = REPO_ROOT / "data" / "archived" / "internships.json"
DEFAULT_SEASON = REPO_ROOT / "config" / "current_season.json"
DEFAULT_README = REPO_ROOT / "README.md"
DEFAULT_INACTIVE = REPO_ROOT / "README-Inactive.md"
DEFAULT_HEALTH = REPO_ROOT / "data" / "health.json"


def format_degree(degree: str) -> str:
    return DEGREE_LABELS.get(degree, "BS/MS")


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_age(when: date, now: date) -> str:
    days = max(0, (now - when).days)
    if days < 30:
        return f"{days}d"
    months = days // 30
    if months < 12:
        return f"{months}mo"
    return f"{days // 365}yr"


def age_for_row(row: dict, now: date) -> str:
    """Posting recency: posted_at else first_seen. Program hubs without posted_at are —."""
    if row.get("row_kind") == "program_fallback" and not row.get("posted_at"):
        return "—"
    raw = row.get("posted_at") or row.get("first_seen")
    if not raw:
        return "—"
    return format_age(parse_iso_date(raw), now)


def load_current_season(path: Path) -> str:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload["season"]


def load_internships(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return []
    return payload


def visible_rows(internships: list[dict], season: str) -> list[dict]:
    return [row for row in internships if row.get("apply_url") and row.get("season") == season]


def season_label(season: str) -> str:
    kind, _, year = season.partition("-")
    if not year:
        return season
    return f"{kind.capitalize()} {year}"


def github_slug(heading: str) -> str:
    slug = heading.lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    return re.sub(r"\s+", "-", slug.strip())


def cell(value: str) -> str:
    return str(value).replace("|", "\\|")


def render_table(rows: list[dict], now: date) -> list[str]:
    ordered = sorted(
        rows,
        key=lambda row: (row.get("company", ""), row.get("title", "")),
    )
    lines = [
        "| Company | Role | Location | Degree | Apply | Age |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in ordered:
        lines.append(
            "| {company} | {title} | {location} | {degree} | {apply} | {age} |".format(
                company=cell(row.get("company", "")),
                title=cell(row.get("title", "")),
                location=cell(row.get("location", "")),
                degree=format_degree(row.get("degree", "unspecified")),
                apply=f"[![Apply](assets/apply.svg)]({row['apply_url']})",
                age=age_for_row(row, now),
            )
        )
    return lines


def grouped_rows(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: list[tuple[str, list[dict]]] = []
    for family in ROLE_FAMILIES:
        family_rows = [row for row in rows if row.get("role_family") == family]
        if family_rows:
            groups.append((family, family_rows))
    return groups


def render_jump_links(groups: list[tuple[str, list[dict]]], season: str) -> list[str]:
    lines = ["## Browse by role", ""]
    if not groups:
        lines.append(f"No listings yet for **{season_label(season)}**.")
        return lines
    links = [
        f"[{family}](#{github_slug(family)}) ({len(family_rows)})" for family, family_rows in groups
    ]
    lines.append(" · ".join(links))
    return lines


def load_health(path: Path) -> dict:
    health_path = Path(path)
    if not health_path.exists():
        return {}
    payload = json.loads(health_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def format_failed_scrapers(names: object) -> str:
    if not names:
        return "—"
    if isinstance(names, list):
        return ", ".join(str(name) for name in names) or "—"
    return str(names)


def generate_readme(
    internships: list[dict],
    *,
    season: str,
    now: date,
    archived_count: int = 0,
    health: dict | None = None,
) -> str:
    """Return README markdown for active internships in ``season``."""
    rows = visible_rows(internships, season)
    groups = grouped_rows(rows)
    label = season_label(season)
    stats = health or {}
    last_sweep = stats.get("last_sweep") or "—"
    updated = stats.get("updated_count")
    updated_cell = "—" if updated is None else str(updated)
    failed_cell = format_failed_scrapers(stats.get("failed_scrapers"))
    archived_cell = stats.get("archived_count", archived_count)
    lines = [
        "# MedTech Internship Radar Catalog",
        "",
        (
            "US STEM internships and summer-shaped co-ops at flagship medical "
            f"device and diabetes companies for **{label}**."
        ),
        "",
    ]
    lines.extend(render_jump_links(groups, season))
    for family, family_rows in groups:
        lines.extend(["", f"## {family}", ""])
        lines.extend(render_table(family_rows, now))
    lines.extend(
        [
            "",
            "## Catalog stats",
            "",
            f"**{len(rows)}** active listings for `{season}`.",
            "",
            "| Last sweep | Updated this sweep | Failed scrapers | Archived |",
            "| --- | --- | --- | --- |",
            f"| {last_sweep} | {updated_cell} | {failed_cell} | {archived_cell} |",
            "",
        ]
    )
    if archived_count:
        lines.extend(
            [
                "Closed listings for this season: [README-Inactive.md](README-Inactive.md).",
                "",
            ]
        )
    if not stats:
        lines.extend(
            [
                "Automation health fields are placeholders until daily refresh lands.",
                "",
            ]
        )
    lines.extend(
        [
            "## Quick Start",
            "",
            (
                "Listings live in [`data/active/internships.json`]"
                "(data/active/internships.json). This README is generated — "
                "do not hand-edit the tables."
            ),
            "",
            "```bash",
            "python scripts/generate_dashboard.py",
            "python scripts/validate_data.py",
            "```",
            "",
            "- Contribute: [CONTRIBUTING.md](CONTRIBUTING.md)",
            "- Schema: [docs/SCHEMA.md](docs/SCHEMA.md)",
            "- Automation: [docs/AUTOMATION.md](docs/AUTOMATION.md)",
            "- Development: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)",
            "- Security: [SECURITY.md](SECURITY.md)",
            "- Maintainer notes: [PLAN.md](PLAN.md) · [HANDOFF.md](HANDOFF.md) · [CONTEXT.md](CONTEXT.md)",
            "",
            "## License",
            "",
            "- Data (`data/`): [CC-BY 4.0](LICENSE-DATA.md)",
            "- Code: [MIT](LICENSE.md)",
            "",
            "See [NOTICE](NOTICE) for the split.",
            "",
        ]
    )
    return "\n".join(lines)


def render_inactive_table(rows: list[dict], now: date) -> list[str]:
    ordered = sorted(
        rows,
        key=lambda row: (row.get("company", ""), row.get("title", "")),
    )
    lines = [
        "| Company | Role | Location | Degree | Apply | Age | Closed | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in ordered:
        lines.append(
            "| {company} | {title} | {location} | {degree} | {apply} | {age} | {closed} | {reason} |".format(
                company=cell(row.get("company", "")),
                title=cell(row.get("title", "")),
                location=cell(row.get("location", "")),
                degree=format_degree(row.get("degree", "unspecified")),
                apply=f"[![Apply](assets/apply.svg)]({row['apply_url']})",
                age=age_for_row(row, now),
                closed=cell(row.get("closed_at") or "—"),
                reason=cell(row.get("close_reason") or "—"),
            )
        )
    return lines


def generate_inactive_readme(
    archived: list[dict],
    *,
    season: str,
    now: date,
) -> str:
    """Return README-Inactive.md for archived rows in ``season``."""
    rows = visible_rows(archived, season)
    label = season_label(season)
    lines = [
        "# Inactive internships",
        "",
        f"Closed listings for **{label}**. These rows left the main README the day they archived.",
        "",
    ]
    if not rows:
        lines.append(f"No archived listings for **{label}**.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(render_inactive_table(rows, now))
    lines.append("")
    return "\n".join(lines)


def write_readme(
    *,
    internships_path: Path = DEFAULT_ACTIVE,
    archived_path: Path = DEFAULT_ARCHIVED,
    season_path: Path = DEFAULT_SEASON,
    readme_path: Path = DEFAULT_README,
    inactive_path: Path = DEFAULT_INACTIVE,
    health_path: Path = DEFAULT_HEALTH,
    now: date | None = None,
) -> str:
    """Load catalog files and write README.md plus README-Inactive.md."""
    clock = date.today() if now is None else now
    internships = load_internships(internships_path)
    archived = load_internships(archived_path) if archived_path.exists() else []
    season = load_current_season(season_path)
    health = load_health(health_path)
    if health:
        health = dict(health)
        health.setdefault("archived_count", len(archived))
    text = generate_readme(
        internships,
        season=season,
        now=clock,
        archived_count=len(archived),
        health=health or None,
    )
    readme_path.write_text(text, encoding="utf-8")
    inactive_path.write_text(
        generate_inactive_readme(archived, season=season, now=clock),
        encoding="utf-8",
    )
    return text


def main(argv: list[str] | None = None) -> int:
    del argv
    write_readme()
    return 0


if __name__ == "__main__":
    sys.exit(main())
