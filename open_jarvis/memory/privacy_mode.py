"""Privacy mode helpers for sensitive sessions."""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_PATTERN = re.compile(r"\b([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*)=([^\s]+)", re.IGNORECASE)
SENSITIVE_KEY_PATTERN = re.compile(r"(key|token|secret|password)", re.IGNORECASE)


def mask_sensitive_text(text: str) -> str:
    """Mask common secret assignments in user-visible text."""

    return SENSITIVE_PATTERN.sub(lambda match: f"{match.group(1)}=***", text)


def mask_sensitive_value(value: Any, key: str | None = None) -> Any:
    """Mask sensitive strings and mapping values before logging."""

    if key and SENSITIVE_KEY_PATTERN.search(key):
        return "***"
    if isinstance(value, str):
        return mask_sensitive_text(value)
    if isinstance(value, dict):
        return {item_key: mask_sensitive_value(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [mask_sensitive_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(mask_sensitive_value(item) for item in value)
    return value


def build_privacy_session(enabled: bool = False) -> dict[str, str | bool]:
    """Return runtime behavior toggles for privacy mode."""

    return {
        "enabled": enabled,
        "memory_writes": "disabled" if enabled else "enabled",
        "retention": "ephemeral" if enabled else "normal",
        "log_masking": "strict" if enabled else "standard",
    }
