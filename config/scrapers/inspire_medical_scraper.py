"""Inspire Medical internship scraper (public Greenhouse Job Board API)."""

from __future__ import annotations

from greenhouse_adapter import GreenhouseInternshipScraper


class InspireMedicalScraper(GreenhouseInternshipScraper):
    """job-boards.greenhouse.io/inspiremedicalsystemsinc via boards-api."""

    company = "Inspire Medical"
    board_slug = "inspiremedicalsystemsinc"
