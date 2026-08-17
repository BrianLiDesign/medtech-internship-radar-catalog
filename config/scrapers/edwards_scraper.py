"""Edwards internship scraper (Algolia InstantSearch public JSON)."""

from algolia_adapter import AlgoliaInternshipScraper


class EdwardsScraper(AlgoliaInternshipScraper):
    """www.edwards.com/careers/jobsearch InstantSearch (Algolia in front of Workday apply URLs)."""

    company = "Edwards"
    application_id = "LTJQZME6D2"
    # Public InstantSearch search-only key from the Edwards jobsearch page (not a secret).
    search_api_key = "beb9bc9bce9e8a52bd34aec0c2b4a599"
    index_name = "EdwardsCareersJobs"
    referer = "https://www.edwards.com/careers/jobsearch"
