"""BD internship scraper (TalentBrew search-jobs JSON)."""

from talentbrew_adapter import TalentBrewInternshipScraper


class BDScraper(TalentBrewInternshipScraper):
    company = "BD"
    origin = "https://jobs.bd.com"
    search_results_module_name = "Section 6 - Search Results List - Content Search"
