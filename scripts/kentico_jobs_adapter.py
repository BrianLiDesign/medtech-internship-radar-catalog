"""Shared Kentico job-search adapter (public HTML partials, not Workday CXS)."""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin

from scraper_framework import InternshipScraper, keep_parsed_posting

PAGE_SIZE = 10
MAX_PAGES = 20


class KenticoJobsInternshipScraper(InternshipScraper):
    """GET {origin}/api/jobs/search?keyword=intern listing HTML."""

    origin: str
    page_url: str
    keywords: str = "intern"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        origin = self.origin.rstrip("/")
        self.headers = {
            **self.headers,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
            "Referer": f"{origin}{self.page_url}",
        }
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        for page in range(1, MAX_PAGES + 1):
            html = self.fetch_text(self._search_url(page))
            if html is None:
                return []
            if not _looks_like_jobs_partial(html):
                self._mark_blocked("unexpected Kentico jobs payload")
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

    def _search_url(self, page: int) -> str:
        query = urlencode(
            {
                "pageUrl": self.page_url,
                "page": page,
                "keyword": self.keywords,
            }
        )
        return f"{self.origin.rstrip('/')}/api/jobs/search?{query}"


def _looks_like_jobs_partial(html: str) -> bool:
    lower = html.lower()
    return (
        "data-partial-count" in lower
        or "data-partial-results" in lower
        or "job-search-table" in lower
    )


def _jobs_from_html(html: str, *, origin: str) -> list[dict]:
    parser = _KenticoJobsTableParser(origin=origin)
    parser.feed(html)
    parser.close()
    return parser.jobs


class _KenticoJobsTableParser(HTMLParser):
    """Extract job-search-table rows. Title, location, and href only."""

    def __init__(self, *, origin: str) -> None:
        super().__init__(convert_charrefs=True)
        self.origin = origin
        self.jobs: list[dict] = []
        self._in_row = False
        self._in_cell = False
        self._in_link = False
        self._href = ""
        self._buf: list[str] = []
        self._cells: list[str] = []
        self._title = ""
        self._title_href = ""
        self._seen_urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: (value or "") for key, value in attrs}
        if tag == "tr":
            self._flush_row()
            self._in_row = True
            self._cells = []
            self._title = ""
            self._title_href = ""
            return
        if not self._in_row:
            return
        if tag == "td":
            self._in_cell = True
            self._buf = []
            return
        if tag == "a":
            href = data.get("href", "").strip()
            if href:
                self._in_link = True
                self._href = href
                self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_link:
            text = " ".join("".join(self._buf).split())
            if text and not self._title:
                self._title = text
                self._title_href = self._href
            self._in_link = False
            self._href = ""
            return
        if tag == "td" and self._in_cell:
            text = " ".join("".join(self._buf).split())
            self._cells.append(text)
            self._in_cell = False
            self._buf = []
            return
        if tag == "tr":
            self._flush_row()

    def handle_data(self, data: str) -> None:
        if self._in_cell or self._in_link:
            self._buf.append(data)

    def close(self) -> None:
        self._flush_row()
        super().close()

    def _flush_row(self) -> None:
        title = self._title
        href = self._title_href
        cells = self._cells
        self._in_row = False
        self._in_cell = False
        self._in_link = False
        self._buf = []
        self._cells = []
        self._title = ""
        self._title_href = ""
        self._href = ""
        if not title or not href:
            return
        apply_url = urljoin(f"{self.origin}/", href)
        if apply_url in self._seen_urls:
            return
        location = cells[-1].strip() if cells else ""
        if not location:
            return
        req_id = ""
        if len(cells) >= 2 and cells[1].strip().upper().startswith("JR-"):
            req_id = cells[1].strip()
        category = cells[2].strip() if len(cells) >= 3 else ""
        self._seen_urls.add(apply_url)
        self.jobs.append(
            {
                "title": title,
                "apply_url": apply_url,
                "location": location,
                "req_id": req_id,
                "posted_at": None,
                "ats": "kentico",
                "short_description": category,
            }
        )
