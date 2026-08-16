"""Shared Eightfold PCSX search adapter (public JSON)."""

from __future__ import annotations

from urllib.parse import urlencode

from scraper_framework import (
    InternshipScraper,
    keep_parsed_posting,
    posted_at_from_unix,
)

PAGE_SIZE = 10
MAX_PAGES = 20
SEARCH_PATH = "/api/pcsx/search"


class EightfoldInternshipScraper(InternshipScraper):
    """GET {careers_origin}/api/pcsx/search?domain=&query=intern."""

    careers_origin: str
    domain: str
    keywords: str = "intern"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        start = 0
        for _page in range(MAX_PAGES):
            payload = self.fetch_json(self._search_url(start=start))
            if payload is None:
                return []
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, dict):
                return list(self._positions_by_url)
            positions = data.get("positions") or []
            if not isinstance(positions, list) or not positions:
                break
            for position in positions:
                if not isinstance(position, dict):
                    continue
                parsed = self._position_to_parsed(position)
                if parsed is None:
                    continue
                self._positions_by_url[parsed["apply_url"]] = parsed
            start += len(positions)
            count = data.get("count")
            if isinstance(count, int) and start >= count:
                break
            if len(positions) < PAGE_SIZE:
                break
        return list(self._positions_by_url)

    def parse_posting(self, url: str) -> dict | None:
        parsed = self._positions_by_url.get(url)
        if parsed is None:
            return None
        if not keep_parsed_posting(parsed):
            return None
        return parsed

    def _search_url(self, start: int) -> str:
        query = urlencode(
            {
                "domain": self.domain,
                "query": self.keywords,
                "start": start,
                "num": PAGE_SIZE,
            }
        )
        return f"{self.careers_origin.rstrip('/')}{SEARCH_PATH}?{query}"

    def _position_to_parsed(self, position: dict) -> dict | None:
        title = str(position.get("name") or "").strip()
        apply_url = self._apply_url(position)
        location = _join_locations(position.get("locations"))
        if not title or not apply_url or not location:
            return None
        req_id = position.get("atsJobId") or position.get("displayJobId") or position.get("id")
        return {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": posted_at_from_unix(
                position.get("postedTs") or position.get("creationTs")
            ),
            "ats": "eightfold",
            "short_description": str(position.get("department") or ""),
        }

    def _apply_url(self, position: dict) -> str:
        origin = self.careers_origin.rstrip("/")
        path = str(position.get("positionUrl") or "").strip()
        if path.startswith("http"):
            return path
        if path.startswith("/"):
            return f"{origin}{path}"
        position_id = position.get("id")
        if position_id is None:
            return ""
        return f"{origin}/careers/job/{position_id}"


def _join_locations(locations: object) -> str:
    if isinstance(locations, str) and locations.strip():
        return _clean_location(locations)
    if not isinstance(locations, list):
        return ""
    cleaned = [_clean_location(item) for item in locations if str(item).strip()]
    return "; ".join(part for part in cleaned if part)


def _clean_location(raw: object) -> str:
    text = str(raw).strip()
    if " | " in text:
        text = text.split(" | ", 1)[0].strip()
    return text
