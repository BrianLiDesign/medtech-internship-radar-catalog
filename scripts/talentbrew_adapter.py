"""Shared TalentBrew career-site search adapter (public JSON wrapping listing HTML)."""

from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin

from scraper_framework import (
    InternshipScraper,
    keep_parsed_posting,
    posted_at_from_iso,
)

PAGE_SIZE = 15
MAX_PAGES = 20


class TalentBrewInternshipScraper(InternshipScraper):
    """GET {origin}/en/search-jobs/results?Keywords=intern (TalentBrew AJAX)."""

    origin: str
    results_path: str = "/en/search-jobs/results"
    search_results_module_name: str = "Search Results"
    keywords: str = "intern"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.headers = {
            **self.headers,
            "Accept": "application/json,text/html;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.origin.rstrip('/')}{self.results_path}",
        }
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        total_pages = 1
        for page in range(1, MAX_PAGES + 1):
            if page > total_pages:
                break
            payload = self.fetch_json(self._search_url(page))
            if payload is None:
                return []
            jobs, pages = _jobs_from_payload(payload, origin=self.origin.rstrip("/"))
            if jobs is None:
                self._mark_blocked("unexpected TalentBrew payload")
                return []
            if pages:
                total_pages = min(pages, MAX_PAGES)
            if not jobs:
                break
            for parsed in jobs:
                self._positions_by_url[parsed["apply_url"]] = parsed
            if page >= total_pages:
                break
        return list(self._positions_by_url)

    def parse_posting(self, url: str) -> dict | None:
        parsed = self._positions_by_url.get(url)
        if parsed is None:
            return None
        if not keep_parsed_posting(parsed):
            return None
        return parsed

    def _search_url(self, page: int) -> str:
        query = urlencode(
            {
                "CurrentPage": page,
                "RecordsPerPage": PAGE_SIZE,
                "DistanceUnit": "Imperial",
                "Keywords": self.keywords,
                "SearchType": "1",
                "SortCriteria": "0",
                "SortDirection": "0",
                "SearchResultsModuleName": self.search_results_module_name,
                "ResultsType": "0",
            }
        )
        return f"{self.origin.rstrip('/')}{self.results_path}?{query}"


def _jobs_from_payload(payload: object, *, origin: str) -> tuple[list | None, int | None]:
    if not isinstance(payload, dict):
        return None, None
    results = payload.get("results")
    if results is None:
        return None, None
    if not isinstance(results, str):
        return None, None
    parser = _TalentBrewResultsParser(origin=origin)
    parser.feed(results)
    parser.close()
    return parser.jobs, parser.total_pages


def _mdy_to_iso(text: str) -> str | None:
    try:
        return datetime.strptime(text.strip(), "%m/%d/%Y").date().isoformat()
    except ValueError:
        return posted_at_from_iso(text)


class _TalentBrewResultsParser(HTMLParser):
    """Extract job-link cards from TalentBrew results HTML. Listing text only."""

    def __init__(self, *, origin: str) -> None:
        super().__init__(convert_charrefs=True)
        self.origin = origin
        self.jobs: list[dict] = []
        self.total_pages: int | None = None
        self._current: dict | None = None
        self._capture: str | None = None
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: (value or "") for key, value in attrs}
        classes = data.get("class", "").split()
        if tag == "section" and data.get("id") == "search-results":
            pages = data.get("data-total-pages", "").strip()
            if pages.isdigit():
                self.total_pages = int(pages)
        if tag == "a" and "job-link" in classes:
            href = data.get("href", "").strip()
            apply_url = urljoin(f"{self.origin}/", href) if href else ""
            req_id = data.get("data-job-id", "").strip()
            self._current = {
                "title": "",
                "apply_url": apply_url,
                "location": "",
                "req_id": req_id,
                "posted_at": None,
                "ats": "talentbrew",
                "short_description": "",
            }
            self._capture = None
            self._buf = []
            return
        if self._current is None:
            return
        if tag == "h2":
            self._capture = "title"
            self._buf = []
        elif tag == "span" and "job-location" in classes:
            self._capture = "location"
            self._buf = []
        elif tag == "span" and "job-date-posted" in classes:
            self._capture = "posted_at"
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if self._current is None:
            return
        if self._capture is not None and tag in {"h2", "span"}:
            text = "".join(self._buf).strip()
            if self._capture == "posted_at":
                self._current["posted_at"] = _mdy_to_iso(text)
            else:
                self._current[self._capture] = text
            self._capture = None
            self._buf = []
        if tag == "a":
            parsed = self._current
            self._current = None
            if (
                parsed
                and parsed.get("title")
                and parsed.get("apply_url")
                and parsed.get("location")
            ):
                self.jobs.append(parsed)

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buf.append(data)
