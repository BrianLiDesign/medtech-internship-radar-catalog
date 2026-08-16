"""Shared SmartRecruiters public postings adapter."""

from __future__ import annotations

from urllib.parse import urlencode

from inclusion import include_posting
from scraper_framework import (
    InternshipScraper,
    keep_parsed_posting,
    posted_at_from_iso,
)

PAGE_SIZE = 100
MAX_PAGES = 20


class SmartRecruitersInternshipScraper(InternshipScraper):
    """GET api.smartrecruiters.com/v1/companies/{identifier}/postings."""

    company_identifier: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        offset = 0
        for _page in range(MAX_PAGES):
            payload = self.fetch_json(self._postings_url(offset))
            if payload is None:
                return []
            jobs = _jobs_from_payload(payload)
            if jobs is None:
                self._mark_blocked("unexpected SmartRecruiters payload")
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
            offset += len(jobs)
            total = payload.get("totalFound")
            if isinstance(total, int) and offset >= total:
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

    def _postings_url(self, offset: int) -> str:
        query = urlencode({"limit": PAGE_SIZE, "offset": offset})
        identifier = self.company_identifier.strip("/")
        return f"https://api.smartrecruiters.com/v1/companies/{identifier}/postings?{query}"

    def _job_to_parsed(self, job: dict) -> dict | None:
        title = str(job.get("name") or "").strip()
        job_id = str(job.get("id") or "").strip()
        if not title or not job_id:
            return None
        location = _smartrecruiters_location(job)
        if not location:
            return None
        apply_url = str(job.get("postingUrl") or job.get("applyUrl") or "").strip()
        if not apply_url:
            apply_url = (
                f"https://jobs.smartrecruiters.com/{self.company_identifier.strip('/')}/{job_id}"
            )
        department = job.get("department")
        if isinstance(department, dict):
            short = str(department.get("label") or department.get("id") or "")
        else:
            short = str(department or "")
        req_id = job.get("refNumber") or job.get("ref") or job_id
        return {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": posted_at_from_iso(job.get("releasedDate")),
            "ats": "smartrecruiters",
            "short_description": short,
        }


def _jobs_from_payload(payload: object) -> list | None:
    if not isinstance(payload, dict):
        return None
    jobs = payload.get("content")
    if jobs is None:
        return []
    if not isinstance(jobs, list):
        return None
    return jobs


def _smartrecruiters_location(job: dict) -> str:
    raw = job.get("location") if isinstance(job.get("location"), dict) else {}
    location = str(raw.get("fullLocation") or "").strip()
    if not location:
        parts = [raw.get("city"), raw.get("region"), raw.get("country")]
        location = ", ".join(str(part).strip() for part in parts if part)
    country = str(raw.get("countryCode") or raw.get("country") or "").strip().lower()
    remote = bool(raw.get("remote"))
    if country not in {"us", "usa", "united states"}:
        return location
    if remote or location.lower() == "remote":
        return "Remote (US)"
    if not location:
        return "United States"
    if include_posting("Software Engineer Intern", location):
        return location
    return f"{location}, United States"
