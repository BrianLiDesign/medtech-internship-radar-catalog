"""Smith+Nephew internship scraper (public US careers hub HTML / JSON-LD)."""

from hub_landing_adapter import HubLandingInternshipScraper


class SmithNephewScraper(HubLandingInternshipScraper):
    """smith-nephew.com US careers intern landing (Workday apply; no CXS)."""

    company = "Smith+Nephew"
    hub_url = "https://www.smith-nephew.com/en-us/careers"
    ats = "workday"
