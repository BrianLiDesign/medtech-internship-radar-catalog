"""Globus Medical internship scraper (public careers hub HTML / JSON-LD)."""

from hub_landing_adapter import HubLandingInternshipScraper


class GlobusMedicalScraper(HubLandingInternshipScraper):
    """globusmedical.com careers co-op landing (Workday apply; no CXS)."""

    company = "Globus Medical"
    hub_url = "https://www.globusmedical.com/about/careers/"
    ats = "workday"
