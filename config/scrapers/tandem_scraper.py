"""Tandem internship scraper (public internship-program hub HTML / JSON-LD)."""

from hub_landing_adapter import HubLandingInternshipScraper


class TandemScraper(HubLandingInternshipScraper):
    """tandemdiabetes.com internship-program landing (Workday apply; no CXS)."""

    company = "Tandem"
    hub_url = "https://www.tandemdiabetes.com/about-us/careers/internship-program"
    ats = "workday"
