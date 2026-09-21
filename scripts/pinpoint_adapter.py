"""Shared Pinpoint job-board adapter (public jobs.json)."""

from __future__ import annotations

from scraper_framework import ListingCacheScraper, posted_at_from_iso


class PinpointInternshipScraper(ListingCacheScraper):
    """GET {jobs_url} Pinpoint board JSON."""

    jobs_url: str

    def populate_listing_cache(self, cache: dict[str, dict]) -> None:
        payload = self.fetch_json(self.jobs_url)
        if payload is None:
            return
        jobs = _jobs_from_payload(payload)
        if jobs is None:
            self._mark_blocked("unexpected Pinpoint payload")
            return
        for job in jobs:
            if not isinstance(job, dict):
                continue
            parsed = self._job_to_parsed(job)
            if parsed is None:
                continue
            cache[parsed["apply_url"]] = parsed

    def _job_to_parsed(self, job: dict) -> dict | None:
        title = str(job.get("title") or "").strip()
        apply_url = str(job.get("url") or "").strip()
        location = _pinpoint_location(job)
        if not title or not apply_url or not location:
            return None
        department = job.get("department")
        if isinstance(department, dict):
            short = str(department.get("name") or department.get("label") or "")
        else:
            short = str(department or "")
        req_id = job.get("requisition_id") or job.get("id")
        return {
            "title": title,
            "apply_url": apply_url,
            "location": location,
            "req_id": str(req_id) if req_id is not None else "",
            "posted_at": posted_at_from_iso(
                job.get("published_at") or job.get("created_at") or job.get("deadline_at")
            ),
            "ats": "pinpoint",
            "short_description": short,
        }


def _jobs_from_payload(payload: object) -> list | None:
    if not isinstance(payload, dict):
        return None
    jobs = payload.get("data")
    if jobs is None:
        return []
    if not isinstance(jobs, list):
        return None
    return jobs


def _pinpoint_location(job: dict) -> str:
    raw = job.get("location")
    if isinstance(raw, dict):
        name = str(raw.get("name") or "").strip()
    else:
        name = str(raw or "").strip()
    if name.upper().startswith("US-"):
        rest = name[3:].replace("_", " ").strip()
        parts = [part for part in rest.split("-") if part]
        if len(parts) >= 2:
            state = parts[0]
            city = " ".join(parts[1:])
            return f"{city}, {state}, United States"
        return f"{rest}, United States" if rest else "United States"
    return name
