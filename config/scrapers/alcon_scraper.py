"""Alcon internship scraper (public early-careers hub HTML / JSON-LD)."""

from hub_landing_adapter import HubLandingInternshipScraper


class AlconScraper(HubLandingInternshipScraper):
    """alcon.com early-careers intern/co-op landing (Workday apply; no CXS)."""

    company = "Alcon"
    hub_url = "https://www.alcon.com/careers/early-careers/"
    ats = "workday"
