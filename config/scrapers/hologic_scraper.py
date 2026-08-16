"""Hologic internship scraper (Oracle Recruiting CE JSON)."""

from oracle_ce_adapter import OracleCEInternshipScraper


class HologicScraper(OracleCEInternshipScraper):
    company = "Hologic"
    origin = "https://ebwb.fa.us2.oraclecloud.com"
    site_number = "CX"
