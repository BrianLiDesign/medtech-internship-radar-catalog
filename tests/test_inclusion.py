"""Shared inclusion classifier — keep or drop a req from title and location."""

from inclusion import include_posting


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


def test_undergraduate_or_graduate_intern_is_kept():
    assert include_posting("Undergraduate or Graduate Intern", "Irvine, CA") is True


def test_remote_us_intern_is_kept():
    assert include_posting("Software Engineer Intern", "Remote (US)") is True


def test_london_uk_intern_is_dropped():
    assert include_posting("Software Engineer Intern", "London, UK") is False


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
