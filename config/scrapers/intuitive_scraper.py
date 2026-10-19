"""Intuitive internship scraper (SmartRecruiters public postings JSON)."""

from scripts.smartrecruiters_adapter import SmartRecruitersInternshipScraper


class IntuitiveScraper(SmartRecruitersInternshipScraper):
    company = "Intuitive"
    company_identifier = "Intuitive"
