"""Inspire Medical internship scraper (public Greenhouse Job Board API)."""

from __future__ import annotations

from scraper_framework import (
    InternshipScraper,
    keep_parsed_posting,
    posted_at_from_iso,
)

JOBS_URL = "https://boards-api.greenhouse.io/v1/boards/inspiremedicalsystemsinc/jobs"


class InspireMedicalScraper(InternshipScraper):
    """job-boards.greenhouse.io/inspiremedicalsystemsinc via boards-api."""

    company = "Inspire Medical"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        payload = self.fetch_json(JOBS_URL)
        if payload is None:
            return []
        if not isinstance(payload, dict):
            self._mark_blocked("unexpected Greenhouse payload")
            return []
        jobs = payload.get("jobs") or []
        if not isinstance(jobs, list):
            self._mark_blocked("unexpected Greenhouse jobs list")
            return []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            parsed = self._job_to_parsed(job)
            if parsed is None:
                continue
            self._positions_by_url[parsed["apply_url"]] = parsed
        return list(self._positions_by_url)

    def parse_posting(self, url: str) -> dict | None:
        parsed = self._positions_by_url.get(url)
        if parsed is None:
            return None
        if not keep_parsed_posting(parsed):
            return None
        return parsed

    def _job_to_parsed(self, job: dict) -> dict | None:
        title = str(job.get("title") or "").strip()
        apply_url = str(job.get("absolute_url") or "").strip()
        location = _greenhouse_location(job)
        if not title or not apply_url or not location:
            return None
        req_id = job.get("requisition_id") or job.get("id")
        parsed = {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": posted_at_from_iso(job.get("first_published") or job.get("updated_at")),
            "ats": "greenhouse",
            "short_description": "",
        }
        return parsed


def _greenhouse_location(job: dict) -> str:
    raw = job.get("location")
    if isinstance(raw, dict):
        return str(raw.get("name") or "").strip()
    return str(raw or "").strip()
