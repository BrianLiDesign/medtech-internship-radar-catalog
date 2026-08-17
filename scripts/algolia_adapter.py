"""Shared Algolia InstantSearch adapter (public search-only JSON, not Workday CXS)."""

from __future__ import annotations

from scraper_framework import InternshipScraper, keep_parsed_posting

PAGE_SIZE = 50
MAX_PAGES = 20


class AlgoliaInternshipScraper(InternshipScraper):
    """POST {appId}-dsn.algolia.net/1/indexes/*/queries for intern-keyword jobs."""

    application_id: str
    search_api_key: str
    index_name: str
    query: str = "intern"
    referer: str = ""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.headers = {
            **self.headers,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-algolia-application-id": self.application_id,
            "x-algolia-api-key": self.search_api_key,
        }
        if self.referer:
            self.headers["Referer"] = self.referer
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        for page in range(MAX_PAGES):
            payload = self.fetch_json(self._search_url(), json_body=self._search_body(page))
            if payload is None:
                return []
            page_result = _first_result(payload)
            if page_result is None:
                self._mark_blocked("unexpected Algolia payload")
                return []
            hits = page_result.get("hits")
            if hits is None:
                hits = []
            if not isinstance(hits, list):
                self._mark_blocked("unexpected Algolia payload")
                return []
            for hit in hits:
                if not isinstance(hit, dict):
                    continue
                parsed = self._job_to_parsed(hit)
                if parsed is None:
                    continue
                self._positions_by_url[parsed["apply_url"]] = parsed
            nb_pages = page_result.get("nbPages")
            try:
                total_pages = int(nb_pages) if nb_pages is not None else 0
            except (TypeError, ValueError):
                total_pages = 0
            if page + 1 >= total_pages or len(hits) < PAGE_SIZE:
                break
        return list(self._positions_by_url)

    def parse_posting(self, url: str) -> dict | None:
        parsed = self._positions_by_url.get(url)
        if parsed is None:
            return None
        if not keep_parsed_posting(parsed):
            return None
        return parsed

    def _search_url(self) -> str:
        app_id = self.application_id.lower()
        return f"https://{app_id}-dsn.algolia.net/1/indexes/*/queries"

    def _search_body(self, page: int) -> dict:
        return {
            "requests": [
                {
                    "indexName": self.index_name,
                    "query": self.query,
                    "hitsPerPage": PAGE_SIZE,
                    "page": page,
                    "analytics": False,
                    "clickAnalytics": False,
                }
            ]
        }

    def _job_to_parsed(self, job: dict) -> dict | None:
        title = str(job.get("JobPostingTitle") or job.get("title") or "").strip()
        apply_url = str(job.get("ApplyUrl") or job.get("applyUrl") or "").strip()
        location = _algolia_location(job)
        if not title or not apply_url or not location:
            return None
        req_id = job.get("id") or job.get("objectID") or job.get("JobRequisition")
        return {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": None,
            "ats": "algolia",
            "short_description": str(job.get("Category") or job.get("EmployeeType") or ""),
        }


def _first_result(payload: object) -> dict | None:
    if not isinstance(payload, dict):
        return None
    results = payload.get("results")
    if not isinstance(results, list):
        return None
    if not results:
        return {}
    first = results[0]
    if not isinstance(first, dict):
        return None
    return first


def _algolia_location(job: dict) -> str:
    location = str(job.get("Location") or job.get("PrimaryJobPostingLocation") or "").strip()
    country = str(job.get("Country") or "").strip()
    if country and country.lower() not in location.lower():
        if location:
            return f"{location}, {country}"
        return country
    return location
