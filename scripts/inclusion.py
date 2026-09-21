"""Shared keep/drop classifier for internship postings (role, season shape, geo)."""

from __future__ import annotations

import re

from geo import is_us_location

_NON_STEM_RE = re.compile(
    r"\bhr\b|human resources|\bmarketing\b|\bsales\b|\bbusiness\b",
    re.IGNORECASE,
)
_OFF_SEASON_RE = re.compile(r"\bfall\b|\bspring\b", re.IGNORECASE)
_ROTATING_RE = re.compile(r"\brotating\b", re.IGNORECASE)
_MULTI_TERM_RE = re.compile(r"\bmulti[\s-]?term\b", re.IGNORECASE)
_PHD_RE = re.compile(r"\bph\.?d\.?\b", re.IGNORECASE)
_INTERN_RE = re.compile(r"\bintern(?:ship)?s?\b", re.IGNORECASE)
_COOP_RE = re.compile(r"\bco-?ops?\b", re.IGNORECASE)
_SUMMER_RE = re.compile(r"\bsummer\b", re.IGNORECASE)


def include_posting(title: str, location: str, **_optional: object) -> bool:
    """Return True if scrapers should keep this req. Extra kwargs are ignored."""
    if _NON_STEM_RE.search(title):
        return False
    if _OFF_SEASON_RE.search(title):
        return False
    if _ROTATING_RE.search(title) or _MULTI_TERM_RE.search(title):
        return False
    if _PHD_RE.search(title):
        return False
    if not _intern_or_summer_coop(title):
        return False
    return is_us_location(location)


def _intern_or_summer_coop(title: str) -> bool:
    if _INTERN_RE.search(title):
        return True
    return bool(_COOP_RE.search(title) and _SUMMER_RE.search(title))
