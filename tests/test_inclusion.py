"""Shared inclusion classifier — keep or drop a req from title and location."""

import pytest
from scripts.inclusion import include_posting


def test_regulatory_affairs_intern_in_the_us_is_kept():
    assert include_posting("Regulatory Affairs Intern", "Minneapolis, MN") is True


def test_hr_intern_is_dropped():
    assert include_posting("HR Intern", "Minneapolis, MN") is False


def test_summer_coop_software_is_kept():
    assert include_posting("Summer Co-op Software", "Boston, MA") is True


def test_fall_coop_is_dropped():
    assert include_posting("Fall Co-op", "Boston, MA") is False


def test_quality_intern_is_kept():
    assert include_posting("Quality Engineer Intern", "Kalamazoo, MI") is True


def test_manufacturing_intern_is_kept():
    assert include_posting("Manufacturing Intern", "Warsaw, IN") is True


def test_marketing_intern_is_dropped():
    assert include_posting("Marketing Intern", "Abbott Park, IL") is False


def test_phd_intern_is_dropped():
    assert include_posting("PhD Intern", "Santa Clara, CA") is False


def test_new_grad_full_time_is_dropped():
    assert include_posting("New Grad Software Engineer", "San Diego, CA") is False


def test_undergraduate_or_graduate_intern_needs_stem_evidence():
    assert not include_posting("Undergraduate or Graduate Intern", "Irvine, CA")
    assert include_posting(
        "Undergraduate or Graduate Intern",
        "Irvine, CA",
        description="Develop embedded software for medical devices.",
    )


@pytest.mark.parametrize(
    "title",
    [
        "Finance GBS Intern",
        "Finance Analyst Intern",
        "Brand Management Intern",
        "People Services Intern",
        "People-Services Intern",
        "Brand Manager Intern",
        "Accounting Intern",
        "Business Intern",
    ],
)
def test_non_stem_roles_rejected_even_with_company_stem_boilerplate(title):
    assert not include_posting(title, "Boston, MA", description="We engineer medical devices.")


@pytest.mark.parametrize(
    "title",
    [
        "Regulatory Affairs Intern",
        "Quality Intern",
        "Manufacturing Intern",
        "Clinical Research Intern",
        "Mechanical Engineering Intern",
        "Data Analyst Intern",
        "Business Intelligence Intern",
        "Software Intern",
        "R&D Intern",
    ],
)
def test_approved_stem_roles_need_neither_year_nor_degree(title):
    assert include_posting(title, "Remote (US)", target_season="summer-2027")


@pytest.mark.parametrize(
    "title,evidence,expected",
    [
        ("Summer 2026 Software Intern", {}, False),
        ("2026 Software Intern", {}, False),
        ("Summer 2027 Software Intern", {}, True),
        ("Software Intern", {"season": "summer-2026"}, False),
        ("Software Intern", {"description": "Internship term: Summer 2026."}, False),
        ("Software Intern", {"description": "Internship term: 2026 Summer."}, False),
        ("Software Intern", {"description": "Summer 2027; graduation in 2028."}, True),
        ("Software Intern", {"description": "Graduate in 2026 or 2028."}, True),
        ("Software Intern", {"season": "spring-2027"}, False),
        ("Summer Software Co-op", {}, True),
        ("Software Co-op", {}, False),
        ("Software Co-op", {"description": "Summer 2027 internship."}, True),
        ("Winter Software Intern", {}, False),
        ("Software Intern", {"description": "Spring 2027 internship."}, False),
    ],
)
def test_season_evidence(title, evidence, expected):
    assert include_posting(title, "Boston, MA", target_season="summer-2027", **evidence) is expected


@pytest.mark.parametrize("degree", ["PhD", "ph.d.", "doctoral", "PhD only"])
def test_supplied_phd_only_degree_is_rejected(degree):
    assert not include_posting("Software Intern", "Boston, MA", degree=degree)


@pytest.mark.parametrize("degree", ["bs", "ms", "bs_ms", "BS/MS/PhD", "Bachelor's or PhD"])
def test_bs_ms_and_mixed_degree_audiences_are_kept(degree):
    assert include_posting("Software Intern", "Boston, MA", degree=degree)


@pytest.mark.parametrize(
    "description,expected",
    [
        ("Must be pursuing a PhD in computer science.", False),
        ("Currently enrolled in a doctoral program.", False),
        ("Requirements: Ph.D. in engineering.", False),
        ("Pursuing a BS, MS, or PhD in engineering.", True),
        ("PhD preferred.", True),
        ("Candidates pursuing a PhD preferred.", True),
        ("Work with PhD scientists on software.", True),
        ("BS completed. Must be enrolled in a PhD program.", False),
        ("<p>Bachelor's degree completed</p><p>Must be pursuing a PhD.</p>", False),
    ],
)
def test_degree_requirements_in_description(description, expected):
    assert include_posting("Research Intern", "Boston, MA", description=description) is expected


def test_mixed_degree_title_and_unknown_degree():
    assert include_posting("BS/MS/PhD Software Intern", "Boston, MA")
    assert include_posting("Software Intern", "Boston, MA", degree="unspecified")


@pytest.mark.parametrize(
    "title,location,evidence,expected",
    [
        ("Intern", "Boston, MA", {}, False),
        ("Analyst Intern", "Boston, MA", {}, False),
        ("Intern", "Boston, MA", {"degree_requirements": "BS in engineering"}, True),
        ("Intern", "Boston, MA", {"description": "Finance work at an engineering company"}, False),
        ("Intern", "Boston, MA", {"short_description": "Manufacturing"}, True),
        ("Software Intern", "", {}, False),
        ("Software Intern", "Remote", {}, False),
    ],
)
def test_missing_and_ambiguous_evidence(title, location, evidence, expected):
    assert include_posting(title, location, **evidence) is expected


def test_target_season_can_advance_without_changing_rules():
    assert include_posting("Summer 2028 Software Intern", "Boston, MA", target_season="summer-2028")
    assert not include_posting(
        "Summer 2027 Software Intern", "Boston, MA", target_season="summer-2028"
    )


def test_remote_us_intern_is_kept():
    assert include_posting("Software Engineer Intern", "Remote (US)") is True


def test_london_uk_intern_is_dropped():
    assert include_posting("Software Engineer Intern", "London, UK") is False


def test_costa_rica_city_starting_with_la_is_not_treated_as_louisiana():
    assert include_posting("Facilities Intern", "La Garita, Costa Rica") is False


def test_rotating_coop_is_dropped():
    assert include_posting("Summer Rotating Co-op Software", "Boston, MA") is False


def test_multi_term_coop_is_dropped():
    assert include_posting("Multi-term Co-op Intern", "Minneapolis, MN") is False


def test_sales_intern_is_dropped():
    assert include_posting("Sales Intern", "Chicago, IL") is False


def test_business_intern_is_dropped():
    assert include_posting("Business Intern", "Abbott Park, IL") is False


def test_spring_only_intern_is_dropped():
    assert include_posting("Spring Intern", "Boston, MA") is False


def test_visa_or_sponsorship_language_does_not_drop_a_us_stem_intern():
    assert (
        include_posting(
            "Software Engineer Intern — no sponsorship / US work authorization required",
            "San Diego, CA",
        )
        is True
    )


@pytest.mark.parametrize(
    "description",
    [
        "Bachelor's degree completed and must be pursuing a doctoral degree.",
        "Education: PhD in engineering.",
    ],
)
def test_prior_bachelors_does_not_make_doctoral_requirement_mixed(description):
    assert not include_posting("Research Intern", "Boston, MA", description=description)


@pytest.mark.parametrize(
    "evidence",
    [
        {"description": "Internship term: Summer of 2026."},
        {"description": "This is a fall internship."},
        {"description": "This is a multi-term co-op."},
    ],
)
def test_explicit_description_term_mismatches(evidence):
    assert not include_posting("Software Intern", "Boston, MA", **evidence)


def test_degree_preference_is_not_a_requirement():
    assert include_posting("Software Intern", "Boston, MA", degree_requirements="PhD preferred")


@pytest.mark.parametrize("pronoun", ["it", "It", "IT"])
def test_pronoun_in_generic_description_is_not_stem_evidence(pronoun):
    assert not include_posting(
        "Intern", "Boston, MA", description=f"{pronoun} is a paid opportunity with our team."
    )


@pytest.mark.parametrize(
    "title,description",
    [
        ("IT Intern", "Join our team."),
        ("IT Support Intern", "Join our team."),
        ("Intern", "Support our information technology team."),
    ],
)
def test_explicit_information_technology_roles_are_stem(title, description):
    assert include_posting(title, "Boston, MA", description=description)


def test_explicit_it_department_is_stem_evidence():
    assert include_posting("Intern", "Boston, MA", short_description="IT")


@pytest.mark.parametrize(
    "requirements",
    [
        "Doctorate required. Bachelor degree completed.",
        "Bachelor degree completed. Doctorate required.",
        "Doctorate required.\nBachelor degree completed.",
    ],
)
def test_prior_education_does_not_cancel_independent_doctoral_requirement(requirements):
    assert not include_posting("Software Intern", "Boston, MA", degree_requirements=requirements)


@pytest.mark.parametrize("field", ["description", "degree_requirements"])
@pytest.mark.parametrize("degree", ["PhD", "Ph.D.", "doctoral"])
def test_unrelated_skill_preference_does_not_cancel_doctoral_enrollment(field, degree):
    assert not include_posting(
        "Software Intern",
        "Boston, MA",
        **{field: f"Currently enrolled in a {degree} program with Python experience preferred."},
    )


@pytest.mark.parametrize("connector", ["is in", "is for", "in", "for"])
@pytest.mark.parametrize("term", ["Fall", "Spring", "Winter"])
def test_compound_off_season_term_is_rejected(connector, term):
    assert not include_posting(
        "Software Intern", "Boston, MA", description=f"This internship {connector} {term}."
    )


def test_compound_summer_term_remains_eligible():
    assert include_posting(
        "Software Intern", "Boston, MA", description="This internship is for Summer 2027."
    )
