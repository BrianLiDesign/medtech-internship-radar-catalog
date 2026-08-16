"""Shared jobs2web career-site search adapter (public listing HTML, not Workday CXS)."""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlparse

from scraper_framework import (
    InternshipScraper,
    keep_parsed_posting,
)

PAGE_SIZE = 25
MAX_PAGES = 20


class Jobs2webInternshipScraper(InternshipScraper):
    """GET {origin}/search/?q=intern (jobs2web listing HTML)."""

    origin: str
    search_path: str = "/search/"
    keywords: str = "intern"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        origin = self.origin.rstrip("/")
        self.headers = {
            **self.headers,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
            "Referer": f"{origin}{self.search_path}",
        }
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        for page in range(MAX_PAGES):
            html = self.fetch_text(self._search_url(page * PAGE_SIZE))
            if html is None:
                return []
            jobs = _jobs_from_html(html, origin=self.origin.rstrip("/"))
            if not jobs:
                break
            new_on_page = 0
            for parsed in jobs:
                url = parsed["apply_url"]
                if url in self._positions_by_url:
                    continue
                self._positions_by_url[url] = parsed
                new_on_page += 1
            if new_on_page == 0 or len(jobs) < PAGE_SIZE:
                break
        return list(self._positions_by_url)

    def parse_posting(self, url: str) -> dict | None:
        parsed = self._positions_by_url.get(url)
        if parsed is None:
            return None
        if not keep_parsed_posting(parsed):
            return None
        return parsed

    def _search_url(self, startrow: int) -> str:
        query = {
            "q": self.keywords,
            "createNewAlert": "false",
        }
        if startrow:
            query["startrow"] = str(startrow)
        return f"{self.origin.rstrip('/')}{self.search_path}?{urlencode(query)}"


def _jobs_from_html(html: str, *, origin: str) -> list[dict]:
    parser = _Jobs2webSearchParser(origin=origin)
    parser.feed(html)
    parser.close()
    return parser.jobs


def _req_id_from_url(apply_url: str) -> str:
    path = urlparse(apply_url).path.rstrip("/")
    segment = path.rsplit("/", 1)[-1]
    return segment if segment.isdigit() else ""


class _Jobs2webSearchParser(HTMLParser):
    """Extract jobTitle-link cards from jobs2web search HTML. Listing text only."""

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
        if tag == "a" and "jobTitle-link" in classes:
            href = data.get("href", "").strip()
            apply_url = urljoin(f"{self.origin}/", href) if href else ""
            if not apply_url:
                return
            if self._current is not None and self._current.get("apply_url") == apply_url:
                if not self._current.get("title"):
                    self._capture = "title"
                    self._buf = []
                return
            self._flush()
            self._current = {
                "title": "",
                "apply_url": apply_url,
                "location": "",
                "req_id": _req_id_from_url(apply_url),
                "posted_at": None,
                "ats": "jobs2web",
                "short_description": "",
            }
            self._capture = "title"
            self._buf = []
            return
        if self._current is None:
            return
        if tag == "span" and "jobLocation" in classes:
            self._capture = "location"
            self._buf = []
            return
        if tag == "div" and data.get("id", "").endswith("-location-value"):
            self._capture = "location"
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if self._capture is None or self._current is None:
            return
        if self._capture == "title" and tag == "a":
            text = " ".join("".join(self._buf).split())
            if text:
                self._current["title"] = text
            self._capture = None
            self._buf = []
            return
        if self._capture == "location" and tag in {"span", "div"}:
            text = " ".join("".join(self._buf).split())
            if text and text.lower() != "location" and not self._current.get("location"):
                self._current["location"] = text
            self._capture = None
            self._buf = []

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
