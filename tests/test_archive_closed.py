"""Archive rules: ATS-closed, two-miss grace, force-close, program-fallback."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from archive_closed import Observation, apply_archive_rules
from generate_dashboard import generate_inactive_readme, generate_readme


def posting(**overrides):
    row = {
        "id": "11111111-1111-4111-8111-111111111111",
        "company": "Boston Scientific",
        "title": "Software Engineer Intern",
        "apply_url": "https://bostonscientific.eightfold.ai/careers/job/563602809367336",
        "season": "summer-2027",
        "role_family": "Software",
        "location": "Marlborough, MA, United States",
        "degree": "unspecified",
        "row_kind": "posting",
        "source": "scrape",
        "first_seen": "2026-08-01",
        "last_seen": "2026-08-13",
        "miss_count": 0,
        "req_id": "627001",
    }
    row.update(overrides)
    return row


def test_posting_one_miss_stays_active():
    row = posting()
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=False)},
    )
    assert [item["id"] for item in active] == [row["id"]]
    assert archived == []
    assert active[0]["miss_count"] == 1
    assert "closed_at" not in active[0]


def test_posting_two_consecutive_misses_archives():
    row = posting(miss_count=1)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=False)},
    )
    assert active == []
    assert len(archived) == 1
    closed = archived[0]
    assert closed["id"] == row["id"]
    assert closed["closed_at"] == "2026-08-14"
    assert closed["close_reason"]
    assert closed["miss_count"] >= 2


def test_ats_closed_archives_immediately():
    row = posting(miss_count=0)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=False, ats_closed=True)},
    )
    assert active == []
    assert len(archived) == 1
    closed = archived[0]
    assert closed["id"] == row["id"]
    assert closed["closed_at"] == "2026-08-14"
    assert closed["close_reason"] == "ats_closed"


def test_posting_html_no_longer_accepting_archives_immediately():
    from unittest.mock import Mock

    response = Mock()
    response.status_code = 200
    response.text = "<html><body>No longer accepting applications.</body></html>"
    session = Mock()
    session.get.return_value = response
    row = posting(miss_count=0, last_seen="2026-08-14")
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        session=session,
    )
    assert active == []
    assert archived[0]["close_reason"] == "ats_closed"
    assert archived[0]["closed_at"] == "2026-08-14"
    session.get.assert_called()


def test_posting_open_html_stays_active_on_same_day_seen():
    from unittest.mock import Mock

    response = Mock()
    response.status_code = 200
    response.text = "<html><body>Apply now for this internship.</body></html>"
    session = Mock()
    session.get.return_value = response
    row = posting(miss_count=0, last_seen="2026-08-14")
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        session=session,
    )
    assert archived == []
    assert [item["id"] for item in active] == [row["id"]]


def test_force_close_archives():
    row = posting(miss_count=0)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=True)},
        force_close_ids=[row["id"]],
    )
    assert active == []
    assert len(archived) == 1
    closed = archived[0]
    assert closed["id"] == row["id"]
    assert closed["closed_at"] == "2026-08-14"
    assert closed["close_reason"] == "force_close"


def fallback(**overrides):
    row = {
        "id": "22222222-2222-4222-8222-222222222222",
        "company": "Medtronic",
        "title": "University internships",
        "apply_url": "https://www.medtronic.com/en-us/our-company/careers/early-careers.html",
        "program_url": "https://www.medtronic.com/en-us/our-company/careers/early-careers.html",
        "season": "summer-2027",
        "role_family": "Other STEM",
        "location": "Minneapolis, MN",
        "degree": "unspecified",
        "row_kind": "program_fallback",
        "source": "seed",
        "first_seen": "2026-08-01",
        "last_seen": "2026-08-13",
        "miss_count": 0,
    }
    row.update(overrides)
    return row


def test_program_fallback_survives_one_miss():
    row = fallback()
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=False, url_status=404)},
    )
    assert archived == []
    assert [item["id"] for item in active] == [row["id"]]
    assert active[0]["miss_count"] == 1
    assert "closed_at" not in active[0]


def test_program_fallback_archives_after_two_url_deaths():
    row = fallback(miss_count=1)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=True, url_status=410)},
    )
    assert active == []
    assert len(archived) == 1
    closed = archived[0]
    assert closed["id"] == row["id"]
    assert closed["closed_at"] == "2026-08-14"
    assert closed["close_reason"] == "url_dead"
    assert closed["miss_count"] >= 2


def test_program_fallback_two_url_deaths_via_mocked_http():
    from unittest.mock import Mock

    response = Mock()
    response.status_code = 404
    session = Mock()
    session.get.return_value = response
    row = fallback(miss_count=1)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        session=session,
    )
    assert active == []
    assert archived[0]["close_reason"] == "url_dead"
    assert session.get.called


def test_archived_row_leaves_main_readme_and_appears_in_inactive():
    row = posting()
    keeper = posting(
        id="33333333-3333-4333-8333-333333333333",
        company="Abbott",
        title="University Internship Program",
        apply_url="https://www.jobs.abbott/us/en/university-internship-program",
        role_family="Other STEM",
        row_kind="program_fallback",
        req_id=None,
    )
    del keeper["req_id"]
    active, archived = apply_archive_rules(
        [row, keeper],
        [],
        today="2026-08-14",
        observations={
            row["id"]: Observation(ats_closed=True),
            keeper["id"]: Observation(seen=True),
        },
    )
    now = date(2026, 8, 14)
    readme = generate_readme(
        active,
        season="summer-2027",
        now=now,
        archived_count=len(archived),
    )
    inactive = generate_inactive_readme(archived, season="summer-2027", now=now)
    assert "Software Engineer Intern" not in readme
    assert "Boston Scientific" not in readme
    assert "University Internship Program" in readme
    assert "Software Engineer Intern" in inactive
    assert "Boston Scientific" in inactive
    assert "closed_at" in str(archived[0]) or "2026-08-14" in inactive
    assert "| 1 |" in readme or "1" in readme.split("Archived")[-1][:80]


def test_duplicate_ids_still_fail_validate_after_archive(tmp_path):
    import json

    from validate_data import validate_catalogs

    schema = json.loads(
        (Path(__file__).resolve().parents[1] / "data" / "schema.json").read_text(encoding="utf-8")
    )
    row = posting()
    _, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(ats_closed=True)},
    )
    active_path = tmp_path / "active.json"
    archived_path = tmp_path / "archived.json"
    active_path.write_text("[]", encoding="utf-8")
    archived_path.write_text(json.dumps([archived[0], dict(archived[0])]), encoding="utf-8")
    errors = validate_catalogs(active_path, archived_path, schema)
    assert errors
    assert any("duplicate" in error.lower() for error in errors)


def test_readme_health_strip_shows_archived_count_after_close():
    row = posting()
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(ats_closed=True)},
    )
    health = {
        "last_sweep": "2026-08-14",
        "updated_count": 2,
        "failed_scrapers": [],
        "archived_count": len(archived),
    }
    readme = generate_readme(
        active,
        season="summer-2027",
        now=date(2026, 8, 14),
        archived_count=len(archived),
        health=health,
    )
    assert "| 2026-08-14 | 2 | — | 1 |" in readme
    assert "placeholders until daily refresh" not in readme


def test_force_close_cli_moves_row_to_archived_file(tmp_path):
    import json

    from archive_closed import main

    row = posting()
    active_path = tmp_path / "active.json"
    archived_path = tmp_path / "archived.json"
    active_path.write_text(json.dumps([row]) + "\n", encoding="utf-8")
    archived_path.write_text("[]\n", encoding="utf-8")
    assert (
        main(
            [
                "--active",
                str(active_path),
                "--archived",
                str(archived_path),
                "--today",
                "2026-08-14",
                "--force-close",
                row["id"],
            ]
        )
        == 0
    )
    assert json.loads(active_path.read_text(encoding="utf-8")) == []
    closed = json.loads(archived_path.read_text(encoding="utf-8"))
    assert len(closed) == 1
    assert closed[0]["id"] == row["id"]
    assert closed[0]["close_reason"] == "force_close"
    assert closed[0]["closed_at"] == "2026-08-14"
