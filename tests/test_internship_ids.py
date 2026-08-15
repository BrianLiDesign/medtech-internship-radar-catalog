"""Internship ID identity — stable UUID v5 for catalog rows."""

import uuid

from internship_ids import CATALOG_NAMESPACE, internship_id

OTHER_CATALOG_NAMESPACE = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")


def test_same_company_and_req_id_yields_the_same_internship_id():
    row = {"company": "Medtronic", "req_id": "R-12345"}
    first = internship_id(row)
    second = internship_id({"company": "Medtronic", "req_id": "R-12345"})
    assert first == second


def test_different_companies_with_the_same_req_id_yield_different_internship_ids():
    medtronic = internship_id({"company": "Medtronic", "req_id": "R-12345"})
    abbott = internship_id({"company": "Abbott", "req_id": "R-12345"})
    assert medtronic != abbott


def test_req_id_wins_over_apply_url():
    with_both = internship_id(
        {
            "company": "Medtronic",
            "req_id": "R-12345",
            "apply_url": "https://jobs.example.com/R-99999",
        }
    )
    req_only = internship_id({"company": "Medtronic", "req_id": "R-12345"})
    url_only = internship_id(
        {
            "company": "Medtronic",
            "apply_url": "https://jobs.example.com/R-99999",
        }
    )
    assert with_both == req_only
    assert with_both != url_only


def test_canonical_apply_url_strips_utm_query_params():
    tracked = internship_id(
        {
            "company": "Dexcom",
            "apply_url": "https://jobs.example.com/intern?utm_source=radar&utm_medium=readme&id=42",
        }
    )
    clean = internship_id(
        {
            "company": "Dexcom",
            "apply_url": "https://jobs.example.com/intern?id=42",
        }
    )
    assert tracked == clean


def test_canonical_apply_url_strips_session_looking_query_params():
    with_session = internship_id(
        {
            "company": "Stryker",
            "apply_url": "https://jobs.example.com/intern?sid=abc&jsessionid=xyz&id=42",
        }
    )
    clean = internship_id(
        {
            "company": "Stryker",
            "apply_url": "https://jobs.example.com/intern?id=42",
        }
    )
    assert with_session == clean


def test_program_fallback_uses_company_and_program_url():
    fallback = internship_id(
        {
            "company": "Intuitive",
            "row_kind": "program_fallback",
            "program_url": "https://careers.intuitive.com/internships",
            "apply_url": "https://careers.intuitive.com/internships?utm_source=radar",
        }
    )
    same_program_different_apply = internship_id(
        {
            "company": "Intuitive",
            "row_kind": "program_fallback",
            "program_url": "https://careers.intuitive.com/internships",
            "apply_url": "https://jobs.example.com/unrelated",
        }
    )
    assert fallback == same_program_different_apply


def test_title_and_location_identity_when_req_id_and_url_are_absent():
    first = internship_id(
        {
            "company": "Abbott",
            "title": "BME Intern",
            "location": "Chicago, IL",
        }
    )
    second = internship_id(
        {
            "company": "Abbott",
            "title": "  BME Intern  ",
            "location": " Chicago, IL ",
        }
    )
    assert first == second


def test_catalog_namespace_is_unique_to_this_catalog():
    assert CATALOG_NAMESPACE != OTHER_CATALOG_NAMESPACE
