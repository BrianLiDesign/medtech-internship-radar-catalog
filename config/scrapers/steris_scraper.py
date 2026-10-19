"""STERIS internship scraper (Phenom widgets JSON)."""

from scripts.phenom_adapter import PhenomInternshipScraper


class SterisScraper(PhenomInternshipScraper):
    company = "STERIS"
    origin = "https://careers.steris.com"
