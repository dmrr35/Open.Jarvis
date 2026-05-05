"""User-facing error message formatting."""

from __future__ import annotations


def build_user_error(title: str, reason: str, fix: str, code: str | None = None) -> str:
    """Render errors in a consistent reason-plus-action format."""

    prefix = f"[{code}] " if code else ""
    return f"{prefix}{title}\nReason: {reason}\nNext step: {fix}"
