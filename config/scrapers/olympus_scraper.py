"""Olympus internship scraper (jobs2web search HTML)."""

from jobs2web_adapter import Jobs2webInternshipScraper


class OlympusScraper(Jobs2webInternshipScraper):
    company = "Olympus"
    origin = "https://careers.olympusamerica.com"
