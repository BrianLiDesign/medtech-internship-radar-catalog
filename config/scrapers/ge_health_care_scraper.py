"""GE HealthCare internship scraper (Phenom widgets JSON)."""

from phenom_adapter import PhenomInternshipScraper


class GEHealthCareScraper(PhenomInternshipScraper):
    company = "GE HealthCare"
    origin = "https://careers.gehealthcare.com"
