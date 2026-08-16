"""Stryker internship scraper (Paradox career-site preload JSON)."""

from __future__ import annotations

import json
from urllib.parse import urlencode

from inclusion import include_posting
from scraper_framework import InternshipScraper, keep_parsed_posting

JOBS_PATH = "/jobs"
ORIGIN = "https://careers.stryker.com"
PRELOAD_MARKER = "window.__PRELOAD_STATE__ = "


class StrykerScraper(InternshipScraper):
    """Parse intern jobs from careers.stryker.com/jobs?keyword=intern preload JSON."""

    company = "Stryker"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.headers = {
            **self.headers,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
            "Referer": f"{ORIGIN}/students-and-graduates",
        }
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        query = urlencode({"keyword": "intern"})
        html = self.fetch_text(f"{ORIGIN}{JOBS_PATH}?{query}")
        if html is None:
            return []
        jobs = _jobs_from_html(html)
        if jobs is None:
            self._mark_blocked("unexpected Stryker preload payload")
            return []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            parsed = _job_to_parsed(job)
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


def _jobs_from_html(html: str) -> list | None:
    start = html.find(PRELOAD_MARKER)
    if start < 0:
        return None
    try:
        payload, _end = json.JSONDecoder().raw_decode(html[start + len(PRELOAD_MARKER) :])
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    search = payload.get("jobSearch")
    if not isinstance(search, dict):
        return None
    jobs = search.get("jobs")
    if jobs is None:
        return []
    if not isinstance(jobs, list):
        return None
    return jobs


def _job_to_parsed(job: dict) -> dict | None:
    title = str(job.get("title") or "").strip()
    apply_url = str(job.get("applyURL") or "").strip()
    location = _stryker_location(job)
    if not title or not apply_url or not location:
        return None
    req_id = job.get("requisitionID") or job.get("reference") or ""
    return {
        "title": title,
        "apply_url": apply_url,
        "location": location,
        "req_id": str(req_id) if req_id else "",
        "posted_at": None,
        "ats": "paradox",
        "short_description": "",
    }


def _stryker_location(job: dict) -> str:
    raw_locations = job.get("locations") if isinstance(job.get("locations"), list) else []
    us_parts: list[str] = []
    other_parts: list[str] = []
    for loc in raw_locations:
        if not isinstance(loc, dict):
            continue
        text = str(loc.get("locationParsedText") or loc.get("locationText") or "").strip()
        country = str(loc.get("countryAbbr") or loc.get("country") or "").strip().lower()
        remote = bool(loc.get("isRemote")) or "remote" in text.lower()
        if country in {"us", "usa", "united states"}:
            if remote:
                return "Remote (US)"
            if text:
                us_parts.append(text)
        elif text:
            other_parts.append(text)
    if us_parts:
        joined = "; ".join(us_parts)
        if include_posting("Software Engineer Intern", joined):
            return joined
        return f"{joined}, United States"
    return "; ".join(other_parts)
