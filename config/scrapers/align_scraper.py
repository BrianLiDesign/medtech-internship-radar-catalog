"""Align internship scraper (Pinpoint public jobs.json)."""

from pinpoint_adapter import PinpointInternshipScraper


class AlignScraper(PinpointInternshipScraper):
    company = "Align"
    jobs_url = "https://jobs.aligntech.com/jobs.json"
