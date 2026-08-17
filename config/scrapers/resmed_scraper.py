"""ResMed internship scraper (public early-careers hub HTML / JSON-LD)."""

from hub_landing_adapter import HubLandingInternshipScraper


class ResMedScraper(HubLandingInternshipScraper):
    """careers.resmed.com early-careers landing (Workday apply; no CXS)."""

    company = "ResMed"
    hub_url = "https://careers.resmed.com/careers/early-careers/"
    ats = "workday"
