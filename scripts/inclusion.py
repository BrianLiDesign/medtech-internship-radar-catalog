"""Shared keep/drop classifier for internship postings (role, season shape, geo)."""

from __future__ import annotations

import re

_US_STATE_ABBR = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD "
    "MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC "
    "SD TN TX UT VT VA WA WV WI WY DC PR".split()
)

_US_STATE_NAME_RE = re.compile(
    r"\b(?:"
    r"alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|"
    r"florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|"
    r"louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|"
    r"missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|"
    r"new york|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|"
    r"rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|"
    r"virginia|washington|west virginia|wisconsin|wyoming|"
    r"district of columbia|puerto rico"
    r")\b",
    re.IGNORECASE,
)
_US_COUNTRY_RE = re.compile(r"\bunited states\b|\bu\.?s\.?a?\.?\b", re.IGNORECASE)
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
_TWO_LETTER_RE = re.compile(r",\s*([A-Za-z]{2})\b")


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
    return _us_location(location)


def _intern_or_summer_coop(title: str) -> bool:
    if _INTERN_RE.search(title):
        return True
    return bool(_COOP_RE.search(title) and _SUMMER_RE.search(title))


def _us_location(location: str) -> bool:
    if _US_COUNTRY_RE.search(location) or _US_STATE_NAME_RE.search(location):
        return True
    return any(token.upper() in _US_STATE_ABBR for token in _TWO_LETTER_RE.findall(location))
