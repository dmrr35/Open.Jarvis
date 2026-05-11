"""Sensitive-value policy for configuration and settings UI surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {
    "GROQ_API_KEY",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_REFRESH_TOKEN",
    "SPOTIFY_ACCESS_TOKEN",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "JARVIS_RELEASE_SIGNING_KEY",
    "JARVIS_PLUGIN_SIGNING_KEY",
    "JARVIS_PLUGIN_SIGNING_KEYS",
}
SENSITIVE_MARKERS = ("API_KEY", "SECRET", "TOKEN", "PASSWORD", "AUTHORIZATION", "BEARER", "PRIVATE_KEY", "SIGNING_KEY")
DEFAULT_SENSITIVE_STATUS_KEYS = (
    "GROQ_API_KEY",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "GEMINI_API_KEY",
    "JARVIS_RELEASE_SIGNING_KEY",
    "JARVIS_PLUGIN_SIGNING_KEY",
    "JARVIS_PLUGIN_SIGNING_KEYS",
)


def is_sensitive_key(key: str) -> bool:
    normalized = key.upper().replace(".", "_")
    return normalized in SENSITIVE_KEYS or any(marker in normalized for marker in SENSITIVE_MARKERS)


def mask_sensitive_setting(value: object) -> str:
    return "configured" if str(value or "").strip() else "missing"


def build_sensitive_status(env: Mapping[str, str], keys: tuple[str, ...] = DEFAULT_SENSITIVE_STATUS_KEYS) -> dict[str, str]:
    return {key: mask_sensitive_setting(env.get(key, "")) for key in keys}


def reject_sensitive_payload(payload: Mapping[str, Any], prefix: str = "") -> list[str]:
    errors: list[str] = []
    for key, value in payload.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        if is_sensitive_key(str(key)) or is_sensitive_key(dotted):
            errors.append(f"Sensitive setting {dotted} is environment-only and cannot be stored in settings.json.")
            continue
        if isinstance(value, Mapping):
            errors.extend(reject_sensitive_payload(value, dotted))
    return errors
