"""Biotronik internship scraper (public North America students hub HTML / JSON-LD)."""

from hub_landing_adapter import HubLandingInternshipScraper


class BiotronikScraper(HubLandingInternshipScraper):
    """biotronik.com North America students landing. Do not follow staging jobs2web."""

    company = "Biotronik"
    hub_url = "https://www.biotronik.com/en-us/careers/career-levels/students"
    ats = "unknown"
