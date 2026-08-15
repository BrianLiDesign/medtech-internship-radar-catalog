"""Penumbra internship scraper (public Lever postings JSON)."""

from __future__ import annotations

from inclusion import include_posting
from scraper_framework import (
    InternshipScraper,
    keep_parsed_posting,
    posted_at_from_unix,
)

POSTINGS_URL = "https://api.lever.co/v0/postings/penumbrainc?mode=json"


class PenumbraScraper(InternshipScraper):
    """jobs.lever.co/penumbrainc via api.lever.co/v0/postings."""

    company = "Penumbra"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        payload = self.fetch_json(POSTINGS_URL)
        if payload is None:
            return []
        if not isinstance(payload, list):
            self._mark_blocked("unexpected Lever payload")
            return []
        for posting in payload:
            if not isinstance(posting, dict):
                continue
            parsed = self._posting_to_parsed(posting)
            if parsed is None:
                continue
            self._positions_by_url[parsed["apply_url"]] = parsed
        return list(self._positions_by_url)

    def parse_posting(self, url: str) -> dict | None:
        parsed = self._positions_by_url.get(url)
        if parsed is None:
            return None
        if not keep_parsed_posting(parsed):
            return None
        return parsed

    def _posting_to_parsed(self, posting: dict) -> dict | None:
        title = str(posting.get("text") or "").strip()
        apply_url = str(posting.get("hostedUrl") or posting.get("applyUrl") or "").strip()
        location = _lever_location(posting)
        if not title or not apply_url or not location:
            return None
        req_id = posting.get("id")
        categories = (
            posting.get("categories") if isinstance(posting.get("categories"), dict) else {}
        )
        parsed = {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": posted_at_from_unix(posting.get("createdAt")),
            "ats": "lever",
            "short_description": str(categories.get("team") or ""),
        }
        return parsed


def _lever_location(posting: dict) -> str:
    categories = posting.get("categories") if isinstance(posting.get("categories"), dict) else {}
    location = str(categories.get("location") or "").strip()
    extras = categories.get("allLocations")
    if isinstance(extras, list):
        parts = [location] if location else []
        for item in extras:
            text = str(item).strip()
            if text and text not in parts:
                parts.append(text)
        location = "; ".join(parts)
    country = str(posting.get("country") or "").strip().upper()
    workplace = str(posting.get("workplaceType") or "").strip().lower().replace("_", "-")
    if country != "US":
        return location
    if workplace == "remote" or location.lower() == "remote":
        return "Remote (US)"
    if not location:
        return "United States"
    if include_posting("Software Engineer Intern", location):
        return location
    return f"{location}, United States"
