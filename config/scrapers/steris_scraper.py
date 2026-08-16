"""STERIS internship scraper (Phenom widgets JSON)."""

from phenom_adapter import PhenomInternshipScraper


class SterisScraper(PhenomInternshipScraper):
    company = "STERIS"
    origin = "https://careers.steris.com"
