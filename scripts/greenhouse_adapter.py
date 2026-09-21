"""Shared Greenhouse job-board adapter (public boards-api JSON)."""

from __future__ import annotations

from scraper_framework import ListingCacheScraper, posted_at_from_iso


class GreenhouseInternshipScraper(ListingCacheScraper):
    """GET boards-api.greenhouse.io/v1/boards/{board_slug}/jobs."""

    board_slug: str

    def populate_listing_cache(self, cache: dict[str, dict]) -> None:
        payload = self.fetch_json(self._jobs_url())
        if payload is None:
            return
        if not isinstance(payload, dict):
            self._mark_blocked("unexpected Greenhouse payload")
            return
        jobs = payload.get("jobs") or []
        if not isinstance(jobs, list):
            self._mark_blocked("unexpected Greenhouse jobs list")
            return
        for job in jobs:
            if not isinstance(job, dict):
                continue
            parsed = self._job_to_parsed(job)
            if parsed is None:
                continue
            cache[parsed["apply_url"]] = parsed

    def _jobs_url(self) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{self.board_slug}/jobs"

    def _job_to_parsed(self, job: dict) -> dict | None:
        title = str(job.get("title") or "").strip()
        apply_url = str(job.get("absolute_url") or "").strip()
        location = _greenhouse_location(job)
        if not title or not apply_url or not location:
            return None
        req_id = job.get("requisition_id") or job.get("id")
        return {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": posted_at_from_iso(job.get("first_published") or job.get("updated_at")),
            "ats": "greenhouse",
            "short_description": "",
        }


def _greenhouse_location(job: dict) -> str:
    raw = job.get("location")
    if isinstance(raw, dict):
        return str(raw.get("name") or "").strip()
    return str(raw or "").strip()
