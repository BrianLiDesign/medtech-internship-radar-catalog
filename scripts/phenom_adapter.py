"""Shared Phenom careers-site widget adapter (public JSON, not Workday CXS)."""

from __future__ import annotations

from scraper_framework import (
    InternshipScraper,
    keep_parsed_posting,
    posted_at_from_iso,
)

PAGE_SIZE = 50
MAX_PAGES = 20


class PhenomInternshipScraper(InternshipScraper):
    """POST {origin}/widgets refineSearch for intern-keyword jobs."""

    origin: str
    keywords: str = "intern"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        origin = self.origin.rstrip("/")
        self.headers = {
            **self.headers,
            "Origin": origin,
            "Referer": f"{origin}/",
        }
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        start = 0
        for _page in range(MAX_PAGES):
            payload = self.fetch_json(self._widgets_url(), json_body=self._search_body(start))
            if payload is None:
                return []
            jobs = _jobs_from_payload(payload)
            if jobs is None:
                self._mark_blocked("unexpected Phenom payload")
                return []
            if not jobs:
                break
            for job in jobs:
                if not isinstance(job, dict):
                    continue
                parsed = self._job_to_parsed(job)
                if parsed is None:
                    continue
                self._positions_by_url[parsed["apply_url"]] = parsed
            if len(jobs) < PAGE_SIZE:
                break
            start += len(jobs)
        return list(self._positions_by_url)

    def parse_posting(self, url: str) -> dict | None:
        parsed = self._positions_by_url.get(url)
        if parsed is None:
            return None
        if not keep_parsed_posting(parsed):
            return None
        return parsed

    def _widgets_url(self) -> str:
        return f"{self.origin.rstrip('/')}/widgets"

    def _search_body(self, start: int) -> dict:
        return {
            "lang": "en_us",
            "deviceType": "desktop",
            "country": "us",
            "pageName": "search-results",
            "ddoKey": "refineSearch",
            "from": start,
            "jobs": True,
            "counts": True,
            "all_fields": ["category", "country", "state", "city", "type"],
            "size": PAGE_SIZE,
            "clearAll": False,
            "jdsource": "facets",
            "isSmartSearch": False,
            "siteType": "external",
            "keywords": self.keywords,
            "global": True,
            "selected_fields": {},
        }

    def _job_to_parsed(self, job: dict) -> dict | None:
        title = str(job.get("title") or "").strip()
        apply_url = str(job.get("applyUrl") or "").strip()
        if not apply_url:
            seq = str(job.get("jobSeqNo") or "").strip()
            if seq:
                apply_url = f"{self.origin.rstrip('/')}/job/{seq}"
        location = _phenom_location(job)
        if not title or not apply_url or not location:
            return None
        req_id = job.get("reqId") or job.get("jobId") or job.get("jobSeqNo")
        return {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": posted_at_from_iso(job.get("postedDate") or job.get("dateCreated")),
            "ats": "phenom",
            "short_description": str(job.get("category") or job.get("type") or ""),
        }


def _jobs_from_payload(payload: object) -> list | None:
    if not isinstance(payload, dict):
        return None
    refine = payload.get("refineSearch")
    if not isinstance(refine, dict):
        return None
    data = refine.get("data")
    if not isinstance(data, dict):
        return None
    jobs = data.get("jobs")
    if jobs is None:
        return []
    if not isinstance(jobs, list):
        return None
    return jobs


def _phenom_location(job: dict) -> str:
    location = ""
    for key in ("cityStateCountry", "cityState", "location"):
        value = str(job.get(key) or "").strip()
        if value:
            location = value
            break
    if not location:
        city = str(job.get("city") or "").strip()
        state = str(job.get("state") or "").strip()
        location = ", ".join(part for part in (city, state) if part)
    country = str(job.get("country") or "").strip()
    if country and country.lower() not in location.lower():
        location = f"{location}, {country}" if location else country
    return location
