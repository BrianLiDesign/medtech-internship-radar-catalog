"""Integra LifeSciences internship scraper (Kentico job-search HTML partials)."""

from kentico_jobs_adapter import KenticoJobsInternshipScraper


class IntegraLifeSciencesScraper(KenticoJobsInternshipScraper):
    """www.integralife.com/careers/job-search intern keyword table (Workday apply URLs)."""

    company = "Integra LifeSciences"
    origin = "https://www.integralife.com"
    page_url = "/careers/job-search"
