"""Shared Oracle Recruiting Cloud Candidate Experience adapter."""

from __future__ import annotations

from urllib.parse import urlencode

from inclusion import include_posting
from scraper_framework import (
    InternshipScraper,
    keep_parsed_posting,
    posted_at_from_iso,
)

PAGE_SIZE = 25
MAX_PAGES = 20


class OracleCEInternshipScraper(InternshipScraper):
    """GET {origin}/hcmRestApi/.../recruitingCEJobRequisitions (public CE JSON)."""

    origin: str
    site_number: str
    keywords: str = "intern"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        start = 0
        for _page in range(MAX_PAGES):
            payload = self.fetch_json(self._search_url(start))
            if payload is None:
                return []
            jobs, total = _jobs_from_payload(payload)
            if jobs is None:
                self._mark_blocked("unexpected Oracle CE payload")
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
            start += len(jobs)
            if isinstance(total, int) and start >= total:
                break
            if len(jobs) < PAGE_SIZE:
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
        finder = (
            f"findReqs;siteNumber={self.site_number},"
            f"keyword={self.keywords},offset={start},limit={PAGE_SIZE}"
        )
        query = urlencode(
            {
                "onlyData": "true",
                "limit": PAGE_SIZE,
                "expand": "requisitionList",
                "finder": finder,
            }
        )
        origin = self.origin.rstrip("/")
        return f"{origin}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?{query}"

    def _job_to_parsed(self, job: dict) -> dict | None:
        title = str(job.get("Title") or "").strip()
        job_id = str(job.get("Id") or "").strip()
        location = _oracle_location(job)
        if not title or not job_id or not location:
            return None
        country = str(job.get("PrimaryLocationCountry") or "").strip().upper()
        if country and country != "US":
            return None
        origin = self.origin.rstrip("/")
        apply_url = f"{origin}/hcmUI/CandidateExperience/en/sites/{self.site_number}/job/{job_id}"
        return {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": job_id,
            "posted_at": posted_at_from_iso(job.get("PostedDate")),
            "ats": "oracle",
            "short_description": str(job.get("JobFamily") or job.get("Department") or ""),
        }


def _jobs_from_payload(payload: object) -> tuple[list | None, int | None]:
    if not isinstance(payload, dict):
        return None, None
    items = payload.get("items")
    if items is None:
        return None, None
    if not isinstance(items, list):
        return None, None
    if not items:
        return [], 0
    first = items[0]
    if not isinstance(first, dict):
        return None, None
    jobs = first.get("requisitionList")
    if jobs is None:
        return [], first.get("TotalJobsCount") if isinstance(
            first.get("TotalJobsCount"), int
        ) else 0
    if not isinstance(jobs, list):
        return None, None
    total = first.get("TotalJobsCount")
    return jobs, total if isinstance(total, int) else None


def _oracle_location(job: dict) -> str:
    location = str(job.get("PrimaryLocation") or "").strip()
    country = str(job.get("PrimaryLocationCountry") or "").strip()
    if country.upper() == "US":
        if include_posting("Software Engineer Intern", location):
            return location or "United States"
        return f"{location}, United States" if location else "United States"
    if country and country.lower() not in location.lower():
        location = f"{location}, {country}" if location else country
    return location
