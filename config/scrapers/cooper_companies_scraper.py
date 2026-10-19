"""CooperCompanies internship scraper (Oracle Recruiting CE JSON)."""

from scripts.oracle_ce_adapter import OracleCEInternshipScraper


class CooperCompaniesScraper(OracleCEInternshipScraper):
    company = "CooperCompanies"
    origin = "https://hcjy.fa.us2.oraclecloud.com"
    site_number = "CX_1"
