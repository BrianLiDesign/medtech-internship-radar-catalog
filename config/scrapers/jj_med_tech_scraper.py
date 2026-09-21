"""J&J MedTech internship scraper (public internships landing HTML)."""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

from scraper_framework import ListingCacheScraper

HUB_URL = "https://www.careers.jnj.com/en/early-career-programs/internships/"
ORIGIN = "https://www.careers.jnj.com"


class JJMedTechScraper(ListingCacheScraper):
    """Parse intern job cards on the public J&J internships landing page."""

    company = "J&J MedTech"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.headers = {
            **self.headers,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
            "Referer": HUB_URL,
        }
    def populate_listing_cache(self, cache: dict[str, dict]) -> None:
        html = self.fetch_text(HUB_URL)
        if html is None:
            return
        for parsed in _jobs_from_html(html, origin=ORIGIN):
            cache[parsed["apply_url"]] = parsed


def _jobs_from_html(html: str, *, origin: str) -> list[dict]:
    parser = _JnjInternshipsParser(origin=origin)
    parser.feed(html)
    parser.close()
    return parser.jobs


class _JnjInternshipsParser(HTMLParser):
    """Extract card-job intern listings. Title, location, and href only."""

    def __init__(self, *, origin: str) -> None:
        super().__init__(convert_charrefs=True)
        self.origin = origin
        self.jobs: list[dict] = []
        self._current: dict | None = None
        self._capture: str | None = None
        self._buf: list[str] = []
        self._seen_urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: (value or "") for key, value in attrs}
        classes = data.get("class", "").split()
        if tag == "li" and "card-job" in classes:
            self._flush()
            self._current = {
                "title": "",
                "apply_url": "",
                "location": "",
                "req_id": data.get("data-id", "").strip(),
                "posted_at": None,
                "ats": "jnj",
                "short_description": "",
            }
            return
        if self._current is None:
            return
        if tag == "a" and "js-view-job" in classes:
            href = data.get("href", "").strip()
            if href:
                self._current["apply_url"] = urljoin(f"{self.origin}/", href)
            self._capture = "title"
            self._buf = []
            return
        if tag == "address" and "PagePromo-location" in classes:
            self._capture = "location"
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if self._capture is not None and self._current is not None:
            if (self._capture == "title" and tag == "a") or (
                self._capture == "location" and tag == "address"
            ):
                text = " ".join("".join(self._buf).split())
                if text:
                    self._current[self._capture] = text
                self._capture = None
                self._buf = []
        if tag == "li":
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buf.append(data)

    def close(self) -> None:
        self._flush()
        super().close()

    def _flush(self) -> None:
        parsed = self._current
        self._current = None
        self._capture = None
        self._buf = []
        if not parsed:
            return
        url = parsed.get("apply_url") or ""
        if parsed.get("title") and url and parsed.get("location") and url not in self._seen_urls:
            self._seen_urls.add(url)
            self.jobs.append(parsed)
