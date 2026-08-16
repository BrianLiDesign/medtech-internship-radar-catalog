"""Teleflex internship scraper (jobs2web search HTML)."""

from jobs2web_adapter import Jobs2webInternshipScraper


class TeleflexScraper(Jobs2webInternshipScraper):
    company = "Teleflex"
    origin = "https://careers.teleflex.com"
