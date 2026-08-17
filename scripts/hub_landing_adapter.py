"""Shared intern-hub landing adapter (JSON-LD JobPosting + intern job cards).

Workday CXS/search is out of scope. Individual job apply URLs with req ids are allowed.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from scraper_framework import InternshipScraper, keep_parsed_posting

_INTERN_RE = re.compile(r"\bintern(?:ship)?s?\b|\bco-?ops?\b", re.IGNORECASE)
_WAF_MARKERS = ("incorrect browser", "access denied")
_JSON_LD_RE = re.compile(
    r"""<script[^>]+type=["']application/ld\+json["'][^>]*>(.*?)</script>""",
    re.IGNORECASE | re.DOTALL,
)


class HubLandingInternshipScraper(InternshipScraper):
    """GET the public intern hub and keep intern-titled job cards / JobPosting JSON-LD."""

    hub_url: str
    ats: str = "unknown"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.headers = {
            **self.headers,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
            "Referer": self.hub_url,
        }
        self._positions_by_url: dict[str, dict] = {}

    def find_posting_urls(self) -> list[str]:
        self._positions_by_url = {}
        html = self.fetch_text(self.hub_url)
        if html is None:
            return []
        if _looks_blocked_html(html):
            self._mark_blocked("browser wall")
            return []
        origin = _origin_from_url(self.hub_url)
        for parsed in _jobs_from_html(html, origin=origin, ats=self.ats, hub_url=self.hub_url):
            self._positions_by_url[parsed["apply_url"]] = parsed
        return list(self._positions_by_url)

    def parse_posting(self, url: str) -> dict | None:
        parsed = self._positions_by_url.get(url)
        if parsed is None:
            return None
        if not keep_parsed_posting(parsed):
            return None
        return parsed


def _jobs_from_html(html: str, *, origin: str, ats: str, hub_url: str) -> list[dict]:
    jobs: list[dict] = []
    seen: set[str] = set()
    for parsed in _jobs_from_json_ld(html, origin=origin, ats=ats, hub_url=hub_url):
        url = parsed["apply_url"]
        if url not in seen:
            seen.add(url)
            jobs.append(parsed)
    for parsed in _jobs_from_anchors(html, origin=origin, ats=ats, hub_url=hub_url):
        url = parsed["apply_url"]
        if url not in seen:
            seen.add(url)
            jobs.append(parsed)
    return jobs


def _jobs_from_json_ld(html: str, *, origin: str, ats: str, hub_url: str) -> list[dict]:
    jobs: list[dict] = []
    for raw in _JSON_LD_RE.findall(html):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for item in _walk_json_ld(payload):
            parsed = _jobposting_to_parsed(item, origin=origin, ats=ats, hub_url=hub_url)
            if parsed is not None:
                jobs.append(parsed)
    return jobs


def _jobs_from_anchors(html: str, *, origin: str, ats: str, hub_url: str) -> list[dict]:
    parser = _HubLandingParser(origin=origin, ats=ats, hub_url=hub_url)
    parser.feed(html)
    parser.close()
    return parser.jobs


def _jobposting_to_parsed(job: dict, *, origin: str, ats: str, hub_url: str) -> dict | None:
    types = job.get("@type")
    type_names = types if isinstance(types, list) else [types]
    if "JobPosting" not in {str(name) for name in type_names}:
        return None
    title = str(job.get("title") or "").strip()
    apply_url = str(job.get("url") or job.get("applicationUrl") or "").strip()
    if apply_url:
        apply_url = urljoin(f"{origin}/", apply_url)
    location = _location_from_jobposting(job)
    if not title or not apply_url or not location:
        return None
    if not _is_job_apply_url(apply_url, hub_url=hub_url):
        return None
    identifier = job.get("identifier")
    req_id = ""
    if isinstance(identifier, dict):
        req_id = str(identifier.get("value") or identifier.get("name") or "").strip()
    elif identifier is not None:
        req_id = str(identifier).strip()
    return {
        "title": title,
        "apply_url": apply_url,
        "location": location,
        "req_id": req_id,
        "posted_at": None,
        "ats": ats,
        "short_description": str(job.get("employmentType") or ""),
    }


def _location_from_jobposting(job: dict) -> str:
    locations = job.get("jobLocation")
    items = locations if isinstance(locations, list) else [locations]
    parts: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        address = item.get("address") if isinstance(item.get("address"), dict) else item
        locality = str(address.get("addressLocality") or "").strip()
        region = str(address.get("addressRegion") or "").strip()
        country = str(address.get("addressCountry") or "").strip()
        chunk = ", ".join(piece for piece in (locality, region, country) if piece)
        if chunk:
            parts.append(chunk)
    if parts:
        return "; ".join(parts)
    remote = str(job.get("jobLocationType") or "").upper()
    if "TELECOMMUTE" in remote:
        return "Remote (US)"
    return ""


def _walk_json_ld(payload: object) -> list[dict]:
    items: list[dict] = []
    if isinstance(payload, list):
        for item in payload:
            items.extend(_walk_json_ld(item))
        return items
    if not isinstance(payload, dict):
        return items
    graph = payload.get("@graph")
    if isinstance(graph, list):
        for item in graph:
            items.extend(_walk_json_ld(item))
        return items
    items.append(payload)
    return items


def _is_job_apply_url(url: str, *, hub_url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if url.rstrip("/") == hub_url.rstrip("/"):
        return False
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    query = parsed.query.lower()
    if "stage." in host or "valhalla" in host:
        return False
    if any(token in path for token in (".pdf", "/people/", "/search")):
        return False
    if "q=" in query or "jobfamilygroup" in query:
        return False
    if "/job/" in path or "/jobs/" in path:
        return True
    if "greenhouse.io" in host or "lever.co" in host:
        return True
    return False


def _looks_blocked_html(html: str) -> bool:
    lower = html.lower()
    return any(marker in lower for marker in _WAF_MARKERS) and len(html) < 4000


def _origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _req_id_from_url(apply_url: str) -> str:
    path = urlparse(apply_url).path.rstrip("/")
    segment = path.rsplit("/", 1)[-1]
    if "_" in segment:
        tail = segment.rsplit("_", 1)[-1]
        if tail and (tail[:1].isalpha() or tail[:1].isdigit()):
            return tail
    return segment if segment.isalnum() else ""


class _HubLandingParser(HTMLParser):
    """Extract intern-titled job anchors plus a nearby location."""

    def __init__(self, *, origin: str, ats: str, hub_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.origin = origin
        self.ats = ats
        self.hub_url = hub_url
        self.jobs: list[dict] = []
        self._current: dict | None = None
        self._capture: str | None = None
        self._buf: list[str] = []
        self._seen_urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: (value or "") for key, value in attrs}
        classes = data.get("class", "").split()
        if tag == "a":
            href = data.get("href", "").strip()
            apply_url = urljoin(f"{self.origin}/", href) if href else ""
            if apply_url and _is_job_apply_url(apply_url, hub_url=self.hub_url):
                self._flush()
                self._current = {
                    "title": "",
                    "apply_url": apply_url,
                    "location": data.get("data-location", "").strip(),
                    "req_id": _req_id_from_url(apply_url),
                    "posted_at": None,
                    "ats": self.ats,
                    "short_description": "",
                }
                self._capture = "title"
                self._buf = []
                return
        if self._current is None:
            return
        if tag in {"span", "div", "address", "p"} and "location" in " ".join(classes).lower():
            self._capture = "location"
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if self._capture is None or self._current is None:
            return
        if self._capture == "title" and tag == "a":
            text = " ".join("".join(self._buf).split())
            if text:
                self._current["title"] = text
            self._capture = None
            self._buf = []
            if not _INTERN_RE.search(self._current.get("title") or ""):
                self._current = None
            return
        if self._capture == "location" and tag in {"span", "div", "address", "p"}:
            text = " ".join("".join(self._buf).split())
            if text and text.lower() != "location" and not self._current.get("location"):
                self._current["location"] = text
            self._capture = None
            self._buf = []

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buf.append(data)

    def close(self) -> None:
        self._flush()
        super().close()

    def _flush(self) -> None:
        parsed = self._current
        self._current = None
        self._capture = None
        self._buf = []
        if not parsed:
            return
        url = parsed.get("apply_url") or ""
        title = parsed.get("title") or ""
        if (
            title
            and url
            and parsed.get("location")
            and _INTERN_RE.search(title)
            and url not in self._seen_urls
        ):
            self._seen_urls.add(url)
            self.jobs.append(parsed)
