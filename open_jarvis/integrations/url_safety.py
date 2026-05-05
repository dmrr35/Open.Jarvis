"""URL normalization and safety checks for browser actions."""

from __future__ import annotations

from urllib.parse import quote_plus, urlparse

ALLOWED_WEB_SCHEMES = {"http", "https"}


def normalize_web_url(url: str) -> str | None:
    """Return a browser-safe URL or None when the scheme is unsafe."""

    value = (url or "").strip()
    if not value:
        return None

    parsed = urlparse(value)
    if not parsed.scheme:
        value = f"https://{value}"
        parsed = urlparse(value)

    if parsed.scheme.lower() not in ALLOWED_WEB_SCHEMES:
        return None
    if not parsed.netloc:
        return None
    return value


def build_google_search_url(query: str) -> str:
    """Build a safe Google search URL."""

    return f"https://www.google.com/search?q={quote_plus(query or '')}"
