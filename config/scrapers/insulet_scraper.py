"""Insulet internship scraper (public students hub HTML / JSON-LD)."""

from hub_landing_adapter import HubLandingInternshipScraper


class InsuletScraper(HubLandingInternshipScraper):
    """insulet.com students-and-early-careers landing (Workday apply; no CXS)."""

    company = "Insulet"
    hub_url = "https://www.insulet.com/working-at-insulet/students-and-early-careers"
    ats = "workday"
