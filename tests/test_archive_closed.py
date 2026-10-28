"""Archive rules: ATS-closed, two-miss grace, force-close, program-fallback."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from scripts.archive_closed import Observation, apply_archive_rules
from scripts.generate_dashboard import generate_inactive_readme, generate_readme


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


@pytest.mark.parametrize("closure", ["seen", "misses", "ats", "force"])
def test_reintroduced_posting_reconciles_existing_archive(closure):
    old = posting(closed_at="2026-08-10", close_reason="consecutive_misses")
    row = posting(
        first_seen="2026-08-12",
        miss_count=1,
        last_miss_on="2026-08-13",
        title="Updated Software Engineer Intern",
        closed_at="2026-08-10",
        close_reason="consecutive_misses",
    )
    unrelated = posting(id="22222222-2222-4222-8222-222222222222")
    active, archived = apply_archive_rules(
        [row],
        [old, unrelated],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=closure == "seen", ats_closed=closure == "ats")},
        force_close_ids=[row["id"]] if closure == "force" else [],
    )
    if closure == "seen":
        assert archived == [unrelated]
        result = active[0]
        assert "closed_at" not in result
        assert "close_reason" not in result
        assert result["miss_count"] == 0
    else:
        assert active == []
        assert len(archived) == 2
        result = next(item for item in archived if item["id"] == row["id"])
        assert result["closed_at"] == "2026-08-14"
        assert (
            result["close_reason"]
            == {
                "misses": "consecutive_misses",
                "ats": "ats_closed",
                "force": "force_close",
            }[closure]
        )
    assert result["first_seen"] == "2026-08-01"
    assert result["title"] == row["title"]
    assert row["first_seen"] == "2026-08-12"
    assert old["closed_at"] == "2026-08-10"


def test_archived_fallback_wins_over_legacy_active_copy():
    row = posting(row_kind="program_fallback")
    closed = dict(row, closed_at="2026-08-10", close_reason="url_dead")
    active, archived = apply_archive_rules(
        [row],
        [closed],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=True, url_status=200)},
    )
    assert active == []
    assert archived == [closed]


def test_posting_two_consecutive_misses_archives():
    row = posting(miss_count=1, last_miss_on="2026-08-13")
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


def test_failed_company_scrape_preserves_existing_miss_count():
    row = posting(miss_count=1)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=False)},
        unavailable_companies={"Boston Scientific"},
    )
    assert archived == []
    assert active[0]["miss_count"] == 1


def test_failed_company_still_archives_a_definitively_dead_posting():
    row = posting(miss_count=1)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=False, url_status=404)},
        unavailable_companies={"Boston Scientific"},
    )
    assert active == []
    assert archived[0]["close_reason"] == "ats_closed"
    assert archived[0]["closed_at"] == "2026-08-14"


def test_failed_company_still_archives_an_ats_closed_posting():
    row = posting(miss_count=1)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(seen=False, ats_closed=True)},
        unavailable_companies={"Boston Scientific"},
    )
    assert active == []
    assert archived[0]["close_reason"] == "ats_closed"
    assert archived[0]["closed_at"] == "2026-08-14"


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


@pytest.mark.parametrize(
    ("checks", "expected_misses", "closed"),
    [
        ([("2026-08-14", 404), ("2026-08-15", 200), ("2026-08-16", 404)], 1, False),
        ([("2026-08-14", 404), ("2026-08-15", 410)], 2, True),
        ([("2026-08-14", 404), ("2026-08-14", 404)], 1, False),
        ([("2026-08-14", 404), ("2026-08-16", 404)], 1, False),
        ([("2026-08-14", 404), ("2026-08-15", None), ("2026-08-16", 404)], 1, False),
        ([("2026-08-14", 404), ("2026-08-14", 200), ("2026-08-14", 404)], 1, False),
    ],
)
def test_fallback_daily_url_transitions(checks, expected_misses, closed):
    row = fallback()
    active, archived = [row], []
    for day, status in checks:
        active, archived = apply_archive_rules(
            active,
            archived,
            today=day,
            observations={row["id"]: Observation(seen=True, url_status=status)},
        )
    assert bool(archived) is closed
    result = (archived if closed else active)[0]
    assert result["miss_count"] == expected_misses
    if closed:
        assert result["close_reason"] == "url_dead"


@pytest.mark.parametrize("status", [None, 301, 403, 408, 429, 500, 503])
def test_fallback_inconclusive_check_preserves_streak(status):
    row = fallback(miss_count=1, last_miss_on="2026-08-14")
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-15",
        observations={row["id"]: Observation(url_status=status)},
    )
    assert archived == []
    assert active == [row]


@pytest.mark.parametrize("status", [200, 204, 299])
def test_fallback_healthy_check_resets_streak(status):
    row = fallback(miss_count=1, last_miss_on="2026-08-14")
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-15",
        observations={row["id"]: Observation(url_status=status)},
    )
    assert archived == []
    assert active[0]["miss_count"] == 0
    assert "last_miss_on" not in active[0]


def test_fallback_undated_legacy_miss_does_not_prove_daily_streak():
    row = fallback(miss_count=1)
    active, archived = apply_archive_rules(
        [row],
        [],
        today="2026-08-14",
        observations={row["id"]: Observation(url_status=404)},
    )
    assert archived == []
    assert active[0]["miss_count"] == 1
    assert active[0]["last_miss_on"] == "2026-08-14"


def test_fallback_timeout_does_not_count_as_url_death():
    from unittest.mock import Mock

    session = Mock()
    session.get.side_effect = TimeoutError("timed out")
    row = fallback(miss_count=1, last_miss_on="2026-08-13")
    active, archived = apply_archive_rules([row], [], today="2026-08-14", session=session)
    assert active == [row]
    assert archived == []
    session.get.assert_called_once()


def test_posting_same_day_rerun_is_not_a_second_daily_miss():
    row = posting()
    active, archived = [row], []
    for day in ["2026-08-14", "2026-08-14"]:
        active, archived = apply_archive_rules(
            active,
            archived,
            today=day,
            observations={row["id"]: Observation(seen=False)},
        )
    assert archived == []
    assert active[0]["miss_count"] == 1
    active, archived = apply_archive_rules(
        active,
        archived,
        today="2026-08-15",
        observations={row["id"]: Observation(seen=False)},
    )
    assert active == []
    assert archived[0]["close_reason"] == "consecutive_misses"


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
    row = fallback(miss_count=1, last_miss_on="2026-08-13")
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
    row = fallback(miss_count=1, last_miss_on="2026-08-13")
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

    from scripts.validate_data import validate_catalogs

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

    from scripts.archive_closed import main

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
