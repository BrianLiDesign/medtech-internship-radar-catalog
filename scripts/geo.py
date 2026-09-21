"""US location classification for scraped posting location strings."""

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
_TWO_LETTER_RE = re.compile(r",\s*([A-Za-z]{2})\b")


def is_us_location(location: str) -> bool:
    """Return True when ``location`` carries enough US geo markers for the catalog."""
    if _US_COUNTRY_RE.search(location) or _US_STATE_NAME_RE.search(location):
        return True
    return any(token.upper() in _US_STATE_ABBR for token in _TWO_LETTER_RE.findall(location))
