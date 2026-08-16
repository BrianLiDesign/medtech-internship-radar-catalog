"""Baxter internship scraper (TalentBrew search-jobs JSON)."""

from talentbrew_adapter import TalentBrewInternshipScraper


class BaxterScraper(TalentBrewInternshipScraper):
    company = "Baxter"
    origin = "https://jobs.baxter.com"
