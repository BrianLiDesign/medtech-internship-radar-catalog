"""Penumbra internship scraper (public Lever postings JSON)."""

from __future__ import annotations

from lever_adapter import LeverInternshipScraper


class PenumbraScraper(LeverInternshipScraper):
    """jobs.lever.co/penumbrainc via api.lever.co/v0/postings."""

    company = "Penumbra"
    board_slug = "penumbrainc"
