"""Siemens Healthineers internship scraper (Phenom widgets JSON)."""

from scripts.phenom_adapter import PhenomInternshipScraper


class SiemensHealthineersScraper(PhenomInternshipScraper):
    company = "Siemens Healthineers"
    origin = "https://careers.siemens-healthineers.com"
