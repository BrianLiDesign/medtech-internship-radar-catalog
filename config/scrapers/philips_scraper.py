"""Philips internship scraper (Phenom widgets JSON)."""

from phenom_adapter import PhenomInternshipScraper


class PhilipsScraper(PhenomInternshipScraper):
    company = "Philips"
    origin = "https://www.careers.philips.com"
