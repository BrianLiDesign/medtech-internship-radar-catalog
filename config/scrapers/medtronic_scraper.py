"""Medtronic internship scraper (public Early Careers hub HTML / JSON-LD)."""

from hub_landing_adapter import HubLandingInternshipScraper


class MedtronicScraper(HubLandingInternshipScraper):
    """www.medtronic.com early-careers intern landing (Workday apply; no CXS)."""

    company = "Medtronic"
    hub_url = "https://www.medtronic.com/en-us/our-company/careers/early-careers.html"
    ats = "workday"
