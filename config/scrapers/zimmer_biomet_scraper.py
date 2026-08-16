"""Zimmer Biomet internship scraper (Phenom widgets JSON)."""

from phenom_adapter import PhenomInternshipScraper


class ZimmerBiometScraper(PhenomInternshipScraper):
    company = "Zimmer Biomet"
    origin = "https://careers.zimmerbiomet.com"
