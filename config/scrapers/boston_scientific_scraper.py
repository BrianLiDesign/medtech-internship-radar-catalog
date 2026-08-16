"""Boston Scientific internship scraper (Eightfold PCSX public JSON)."""

from eightfold_adapter import EightfoldInternshipScraper


class BostonScientificScraper(EightfoldInternshipScraper):
    """bostonscientific.eightfold.ai PCSX search."""

    company = "Boston Scientific"
    careers_origin = "https://bostonscientific.eightfold.ai"
    domain = "bostonscientific.com"
