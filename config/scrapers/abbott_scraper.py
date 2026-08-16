"""Abbott internship scraper (Phenom widgets JSON)."""

from phenom_adapter import PhenomInternshipScraper


class AbbottScraper(PhenomInternshipScraper):
    """www.jobs.abbott public intern search (Phenom in front of Workday apply URLs)."""

    company = "Abbott"
    origin = "https://www.jobs.abbott"
