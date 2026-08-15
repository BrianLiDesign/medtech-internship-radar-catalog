"""Deterministic UUID v5 identity for internship catalog rows."""

from __future__ import annotations

import uuid
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CATALOG_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "medtech-internship-radar-catalog")

_SESSION_QUERY_PARAMS = frozenset({"sid", "sessionid", "jsessionid", "session", "phpsessid"})


def canonical_apply_url(url: str) -> str:
    """Strip tracking query params so apply URLs can be used as identity."""
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not _is_tracking_or_session_param(key)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _is_tracking_or_session_param(key: str) -> bool:
    lowered = key.lower()
    return lowered.startswith("utm_") or lowered in _SESSION_QUERY_PARAMS


def internship_id(row: dict) -> str:
    """Return a stable UUID v5 for an internship row."""
    company = row["company"].strip().lower()
    req_id = row.get("req_id")
    apply_url = row.get("apply_url")
    if req_id:
        key = f"{company}|{req_id}"
    elif row.get("row_kind") == "program_fallback" and row.get("program_url"):
        key = f"{company}|{row['program_url']}"
    elif apply_url:
        key = f"{company}|{canonical_apply_url(apply_url)}"
    else:
        title = row["title"].strip().lower()
        location = row["location"].strip().lower()
        key = f"{company}|{title}|{location}"
    return str(uuid.uuid5(CATALOG_NAMESPACE, key))
