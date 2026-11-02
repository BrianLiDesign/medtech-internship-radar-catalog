"""Decision contract and invariants, independent of the parsing implementation."""

import json
from pathlib import Path

import pytest
from scripts.inclusion import classify_posting, include_posting

CASES = json.loads(
    (Path(__file__).parent / "fixtures/qualification_decisions.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_decision_contract(case):
    title = case.get("title", "Software Intern")
    decision = classify_posting(title, "Boston, MA", description=case["text"])
    assert decision.outcome == case["outcome"]
    assert include_posting(title, "Boston, MA", description=case["text"]) == (
        case["outcome"] == "accept"
    )


@pytest.mark.parametrize(
    "degree,outcome", [("PhD preferred", "accept"), ("PhD required", "reject")]
)
@pytest.mark.parametrize(
    "skill",
    [
        "Python required",
        "Python preferred",
        "MS Office required",
        "Microsoft Office required",
        "Required Java skills",
        "Communication skills required",
    ],
)
@pytest.mark.parametrize("separator", ["; ", ". ", "\n", " and ", " with ", ", "])
def test_unrelated_qualification_cannot_change_degree_decision(degree, outcome, skill, separator):
    for text in (degree + separator + skill, skill + separator + degree):
        assert (
            classify_posting("Software Intern", "Boston, MA", description=text).outcome == outcome
        )


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_equivalent_html_and_field_order(case):
    text = case["text"]
    html = "<div>" + text.replace("\n", "</div><div>").replace("PhD", "<b>PhD</b>") + "</div>"
    for evidence in (
        {"details": text, "other": "Python required."},
        {"other": "Python required.", "details": html},
    ):
        assert (
            classify_posting(
                case.get("title", "Software Intern"), "Boston, MA", description=evidence
            ).outcome
            == case["outcome"]
        )


def test_evidence_retains_local_modality_and_source():
    decision = classify_posting(
        "Software Intern",
        "Boston, MA",
        description={"qualifications": "PhD preferred and Python required."},
    )
    degree = next(item for item in decision.qualifications if item.credentials == ("PhD",))
    skill = next(item for item in decision.qualifications if "Python" in item.clause)
    assert degree.modality == "preferred"
    assert skill.modality == "required"
    assert degree.source == "description.qualifications"
    assert degree.clause == "PhD preferred"
    assert degree.source_clause == "PhD preferred and Python required"


@pytest.mark.parametrize("office", ["MS Office", "Microsoft Office"])
def test_office_is_recorded_as_skill_evidence(office):
    decision = classify_posting(
        "Software Intern", "Boston, MA", description=f"PhD required and {office} preferred."
    )
    skill = next(item for item in decision.qualifications if office in item.clause)
    assert skill.credentials == ()
    assert skill.modality == "preferred"
    assert skill.skill == office + " preferred"


@pytest.mark.parametrize(
    "heading", ["Preferred Qualifications", "preferred qualifications", "PREFERRED QUALIFICATIONS"]
)
def test_heading_scope_survives_ats_structure_and_inline_layout(heading):
    for value in (
        {"lists": [{"text": heading, "content": "PhD"}]},
        heading + "\nPython\nPhD",
        heading + ": Python\nPhD",
        "<h3>" + heading + "</h3><ul><li>Python</li><li>PhD</li></ul>",
    ):
        assert (
            classify_posting("Software Intern", "Boston, MA", description=value).outcome == "accept"
        )


@pytest.mark.parametrize(
    "text",
    [
        "Pursuing a BS and/or PhD.",
        "Must be pursuing a Bachelor's degree or a PhD in engineering.",
    ],
)
def test_explicit_credential_relations_are_alternatives(text):
    assert classify_posting("Software Intern", "Boston, MA", description=text).outcome == "accept"


@pytest.mark.parametrize("spelling", ["PhD", "Ph.D.", "ph.D.", "Ph. D."])
@pytest.mark.parametrize(
    "template,outcome",
    [
        ("{} required. Python preferred.", "reject"),
        ("Preferred qualifications:\n{}\nRequired qualifications:\nPython", "accept"),
        ("{} preferred. Python required.", "accept"),
    ],
)
def test_credential_spelling_preserves_scope(spelling, template, outcome):
    assert (
        classify_posting(
            "Software Intern", "Boston, MA", description=template.format(spelling)
        ).outcome
        == outcome
    )


@pytest.mark.parametrize("level", range(1, 7))
def test_all_heading_levels_preserve_required_and_preferred_sections(level):
    for degree_modality, outcome in [("Required", "reject"), ("Preferred", "accept")]:
        text = f"<h{level}>{degree_modality} qualifications: PhD</h{level}><h{level}>Required qualifications: Python</h{level}>"
        assert (
            classify_posting("Software Intern", "Boston, MA", description=text).outcome == outcome
        )


@pytest.mark.parametrize(
    "description,outcome",
    [
        ("Must have legal authorization to work in the United States.", "accept"),
        ("Finance work. Must have legal authorization to work in the United States.", "reject"),
        ("Work in our legal department.", "reject"),
    ],
)
def test_authorization_is_not_role_evidence(description, outcome):
    assert (
        classify_posting(
            "Intern", "Boston, MA", short_description="Software", description=description
        ).outcome
        == outcome
    )


def test_applicant_and_colleague_credentials_keep_separate_evidence():
    result = classify_posting(
        "Software Intern", "Boston, MA", description="Must have a PhD to work with PhD scientists."
    )
    degrees = [q for q in result.qualifications if "PhD" in q.credentials]
    assert [q.modality for q in degrees] == ["required", "mentioned"]


@pytest.mark.parametrize(
    "predicate",
    ["is not optional", "is never optional", "isn't optional", "is not an optional qualification"],
)
def test_negation_binds_to_optionality(predicate):
    assert (
        classify_posting("Software Intern", "Boston, MA", description=f"A PhD {predicate}.").outcome
        == "reject"
    )


@pytest.mark.parametrize(
    "authorization",
    [
        "legal authorization",
        "legal right",
        "legal work authorization",
        "legal permanent resident status",
        "legal US work authorization",
        "legal U.S. work authorization",
        "legal United States employment authorization",
    ],
)
def test_work_authorization_variants_do_not_affect_stem_role(authorization):
    assert (
        classify_posting(
            "Intern",
            "Boston, MA",
            short_description="Software",
            description=f"Must have {authorization} to work here.",
        ).outcome
        == "accept"
    )


@pytest.mark.parametrize(
    "placement,expected",
    [("Summer 2027", "accept"), ("Summer 2026", "reject"), ("Fall 2027", "reject")],
)
def test_graduation_context_does_not_hide_a_placement_term(placement, expected):
    for text in (
        f"Expected graduation: Spring 2028. Internship term: {placement}.",
        f"Internship term: {placement}. Expected graduation: Spring 2028.",
        f"Graduating in Spring 2028 for a {placement} internship.",
        f"Expected graduation:\nSpring 2028\nInternship term: {placement}.",
    ):
        assert (
            classify_posting("Software Intern", "Boston, MA", description=text).outcome == expected
        )
