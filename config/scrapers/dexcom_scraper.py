"""Dexcom internship scraper (Eightfold PCSX public JSON)."""

from scripts.eightfold_adapter import EightfoldInternshipScraper


class DexcomScraper(EightfoldInternshipScraper):
    company = "Dexcom"
    careers_origin = "https://careers.dexcom.com"
    domain = "dexcom.com"
