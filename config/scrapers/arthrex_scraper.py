"""Arthrex internship scraper (jobs2web search HTML)."""

from jobs2web_adapter import Jobs2webInternshipScraper


class ArthrexScraper(Jobs2webInternshipScraper):
    company = "Arthrex"
    origin = "https://careers.arthrex.com"
