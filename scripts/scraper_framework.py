"""Internship-native scraper framework: discovery, fetch, merge, soft-fail."""

from __future__ import annotations

import importlib.util
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

from inclusion import include_posting
from internship_ids import canonical_apply_url, internship_id

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCRAPERS_DIR = REPO_ROOT / "config" / "scrapers"
DEFAULT_SEASON_FILE = REPO_ROOT / "config" / "current_season.json"
DEFAULT_TIMEOUT = 15.0
DEFAULT_RATE_LIMIT = 1.0

_SOFTWARE_MARKERS = ("software", "swe", "computer science", "frontend", "backend", "full stack")
_DATA_MARKERS = ("data", "machine learning", " ml", "ml ", "artificial intelligence")
_ELECTRICAL_MARKERS = ("electrical", "firmware", "embedded")
_MECHANICAL_MARKERS = ("mechanical", "robotic")
_QUALITY_MARKERS = ("quality", "manufacturing", "operations", "supply chain")
_BME_MARKERS = ("r&d", "r and d", "biomed", "bme", "research", "systems engineering", "scientist")


@dataclass
class ScrapeResult:
    """Outcome of one company scrape. Empty postings on soft-fail — never invented."""

    company: str
    postings: list[dict] = field(default_factory=list)
    blocked: bool = False
    error: str | None = None


class InternshipScraper(ABC):
    """Base class for allowlisted company internship scrapers."""

    company: str

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT,
        artifact_path: Path | None = None,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.artifact_path = artifact_path
        self._last_request_at = 0.0
        self._blocked = False
        self._error: str | None = None
        self.headers = {
            "Accept": "application/json,text/html;q=0.9",
            "User-Agent": "MedTechInternshipRadar/0.1 (catalog refresh)",
        }

    @abstractmethod
    def find_posting_urls(self) -> list[str]:
        """Return apply URLs (or listing keys) for candidate postings."""

    @abstractmethod
    def parse_posting(self, url: str) -> dict | None:
        """Parse one posting into a catalog-shaped dict, or None if invalid."""

    def scrape(self, seen_on: str, season: str | None = None) -> ScrapeResult:
        """Fetch postings and map them into schema rows. Soft-fail yields no rows."""
        self._blocked = False
        self._error = None
        urls = self.find_posting_urls()
        if self._blocked:
            self.write_failure_artifact()
            return ScrapeResult(
                company=self.company,
                postings=[],
                blocked=True,
                error=self._error,
            )
        catalog_season = season or _current_season()
        postings: list[dict] = []
        for url in urls:
            parsed = self.parse_posting(url)
            if not parsed:
                continue
            postings.append(self.to_catalog_row(parsed, seen_on=seen_on, season=catalog_season))
        return ScrapeResult(company=self.company, postings=postings)

    def fetch_json(self, url: str):
        """GET JSON with timeout and rate limit. Blocked responses yield None.

        Lever boards return a JSON array; Greenhouse/Eightfold return objects.
        """
        self._wait_for_rate_limit()
        try:
            response = self.session.get(url, timeout=self.timeout, headers=self.headers)
        except Exception as exc:
            self._mark_blocked(str(exc))
            return None
        status = getattr(response, "status_code", 0)
        if status in (401, 403, 429) or status >= 500:
            self._mark_blocked(f"HTTP {status}")
            return None
        if status >= 400:
            self._mark_blocked(f"HTTP {status}")
            return None
        try:
            payload = response.json()
        except Exception as exc:
            self._mark_blocked(f"invalid JSON: {exc}")
            return None
        if _looks_unauthorized(payload):
            self._mark_blocked("not authorized")
            return None
        return payload

    def to_catalog_row(self, parsed: dict, *, seen_on: str, season: str) -> dict:
        """Map a parsed posting onto a schema-complete catalog row."""
        apply_url = parsed["apply_url"]
        title = parsed["title"]
        location = parsed["location"]
        tag_text = " ".join(
            part
            for part in (
                title,
                parsed.get("short_description") or "",
                parsed.get("description") or "",
            )
            if part
        )
        row = {
            "id": "",
            "company": self.company,
            "title": title,
            "apply_url": apply_url,
            "season": season,
            "role_family": parsed.get("role_family") or role_family_for_title(title),
            "location": location,
            "degree": parsed.get("degree") or "unspecified",
            "row_kind": "posting",
            "source": "scrape",
            "first_seen": seen_on,
            "last_seen": seen_on,
            "work_auth": parsed.get("work_auth") or parse_work_auth(tag_text),
            "eligibility": parsed.get("eligibility") or parse_eligibility(tag_text),
            "miss_count": 0,
            "canonical_apply_url": canonical_apply_url(apply_url),
            "ats": parsed.get("ats") or "unknown",
            "short_description": parsed.get("short_description") or "",
        }
        if parsed.get("req_id"):
            row["req_id"] = str(parsed["req_id"])
        if parsed.get("posted_at"):
            row["posted_at"] = parsed["posted_at"]
        row["id"] = internship_id(row)
        return row

    def write_failure_artifact(self) -> None:
        if self.artifact_path is None:
            return
        path = Path(self.artifact_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "company": self.company,
            "blocked": True,
            "error": self._error,
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _wait_for_rate_limit(self) -> None:
        if self.rate_limit_delay <= 0:
            self._last_request_at = time.monotonic()
            return
        elapsed = time.monotonic() - self._last_request_at
        if self._last_request_at and elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_at = time.monotonic()

    def _mark_blocked(self, error: str) -> None:
        self._blocked = True
        self._error = error


def discover_scrapers(scrapers_dir: Path | None = None) -> dict[str, type[InternshipScraper]]:
    """Register subclasses named *Scraper from config/scrapers/."""
    directory = Path(scrapers_dir or DEFAULT_SCRAPERS_DIR)
    found: dict[str, type[InternshipScraper]] = {}
    if not directory.is_dir():
        return found
    for path in sorted(directory.glob("*_scraper.py")):
        module = _load_module(path)
        for name, obj in vars(module).items():
            if not _is_company_scraper(name, obj):
                continue
            company = getattr(obj, "company", "") or _company_from_class_name(name)
            found[company] = obj
    return found


def upsert_catalog(existing: list[dict], scraped: list[dict], seen_on: str) -> list[dict]:
    """Merge scraped postings by internship ID. Freeze first_seen; update last_seen."""
    incoming = {row["id"]: row for row in scraped}
    scraped_companies = {row["company"] for row in scraped if row.get("row_kind") == "posting"}
    merged: list[dict] = []
    seen_ids: set[str] = set()
    for old in existing:
        if old["id"] in incoming:
            updated = dict(incoming[old["id"]])
            updated["first_seen"] = old["first_seen"]
            updated["last_seen"] = seen_on
            updated["source"] = "scrape"
            merged.append(updated)
            seen_ids.add(old["id"])
            continue
        if old.get("row_kind") == "program_fallback" and old.get("company") in scraped_companies:
            continue
        merged.append(old)
        seen_ids.add(old["id"])
    for row in scraped:
        if row["id"] in seen_ids:
            continue
        added = dict(row)
        added["first_seen"] = row.get("first_seen") or seen_on
        added["last_seen"] = seen_on
        added["source"] = "scrape"
        merged.append(added)
    return merged


def role_family_for_title(title: str) -> str:
    """Map a posting title onto a README role-family enum."""
    lower = title.lower()
    if any(marker in lower for marker in _SOFTWARE_MARKERS):
        return "Software"
    if any(marker in lower for marker in _DATA_MARKERS):
        return "Data/ML"
    if any(marker in lower for marker in _ELECTRICAL_MARKERS):
        return "Electrical/firmware"
    if any(marker in lower for marker in _MECHANICAL_MARKERS):
        return "Mechanical/robotics"
    if any(marker in lower for marker in _QUALITY_MARKERS):
        return "Quality/manufacturing"
    if any(marker in lower for marker in _BME_MARKERS):
        return "BME/R&D"
    return "Other STEM"


def parse_eligibility(text: str) -> str:
    """Best-effort eligibility tag. Never used to drop a row."""
    lower = text.lower()
    if "returning" in lower or "internal only" in lower:
        return "returning"
    return "open"


def parse_work_auth(text: str) -> str:
    """Best-effort work-auth tag. Never used to drop a row."""
    lower = text.lower()
    if "citizen" in lower:
        return "citizen_only"
    if "no sponsorship" in lower or "not sponsor" in lower or "does not sponsor" in lower:
        return "us_auth_no_sponsor"
    return "unspecified"


def posted_at_from_unix(timestamp: object) -> str | None:
    try:
        value = int(timestamp)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if abs(value) >= 10_000_000_000:
        value //= 1000
    return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()


def posted_at_from_iso(value: object) -> str | None:
    """Take YYYY-MM-DD from an ISO-8601 timestamp (Python 3.9-safe)."""
    text = str(value or "").strip()
    if len(text) < 10 or text[4] != "-" or text[7] != "-":
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def keep_parsed_posting(parsed: dict) -> bool:
    """Apply the shared inclusion classifier to a parsed posting."""
    return include_posting(parsed.get("title", ""), parsed.get("location", ""))


def _current_season(path: Path = DEFAULT_SEASON_FILE) -> str:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload["season"]


def _looks_unauthorized(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    message = str(payload.get("message") or "").lower()
    return "not authorized" in message


def _is_company_scraper(name: str, obj: object) -> bool:
    return (
        isinstance(obj, type)
        and issubclass(obj, InternshipScraper)
        and obj is not InternshipScraper
        and name.endswith("Scraper")
    )


def _company_from_class_name(class_name: str) -> str:
    stem = class_name[: -len("Scraper")]
    chars: list[str] = []
    for index, char in enumerate(stem):
        if index and char.isupper() and not stem[index - 1].isupper():
            chars.append(" ")
        chars.append(char)
    return "".join(chars)


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load scraper module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
