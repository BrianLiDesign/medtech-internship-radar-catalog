"""CONMED internship scraper (Phenom widgets JSON)."""

from phenom_adapter import PhenomInternshipScraper


class ConmedScraper(PhenomInternshipScraper):
    company = "CONMED"
    origin = "https://careers.conmed.com"
