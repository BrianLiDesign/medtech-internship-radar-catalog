"""Shared Lever job-board adapter (public postings JSON)."""

from __future__ import annotations

from geo import is_us_location
from scraper_framework import ListingCacheScraper, posted_at_from_unix


class LeverInternshipScraper(ListingCacheScraper):
    """GET api.lever.co/v0/postings/{board_slug}?mode=json."""

    board_slug: str

    def populate_listing_cache(self, cache: dict[str, dict]) -> None:
        payload = self.fetch_json(self._postings_url())
        if payload is None:
            return
        if not isinstance(payload, list):
            self._mark_blocked("unexpected Lever payload")
            return
        for posting in payload:
            if not isinstance(posting, dict):
                continue
            parsed = self._posting_to_parsed(posting)
            if parsed is None:
                continue
            cache[parsed["apply_url"]] = parsed

    def _postings_url(self) -> str:
        return f"https://api.lever.co/v0/postings/{self.board_slug}?mode=json"

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
        return {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": posted_at_from_unix(posting.get("createdAt")),
            "ats": "lever",
            "short_description": str(categories.get("team") or ""),
        }


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
    if is_us_location(location):
        return location
    return f"{location}, United States"
