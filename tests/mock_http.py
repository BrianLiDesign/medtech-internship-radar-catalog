"""Shared mock HTTP sessions for scraper tests."""

from __future__ import annotations

import json
from unittest.mock import Mock


def json_session(payload, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = {"Content-Type": "application/json"}
    response.text = json.dumps(payload)
    response.json.return_value = payload
    session = Mock()
    session.get.return_value = response
    session.post.return_value = response
    return session


def html_session(html: str, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.headers = {"Content-Type": "text/html; charset=utf-8"}
    response.text = html
    response.json.side_effect = ValueError("not json")
    session = Mock()
    session.get.return_value = response
    session.post.return_value = response
    return session
