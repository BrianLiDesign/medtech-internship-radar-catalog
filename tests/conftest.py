"""Pytest hooks and shared mock HTTP helpers for scraper tests."""

from __future__ import annotations

from tests.mock_http import html_session, json_session

__all__ = ["html_session", "json_session"]
