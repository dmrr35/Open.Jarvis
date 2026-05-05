"""User profile helpers for per-user settings and memory isolation."""

from __future__ import annotations

import copy
from typing import Any

DEFAULT_SETTINGS = {
    "wake_word": "jarvis",
    "permission_profile": "normal",
    "privacy_mode": False,
}


def build_user_profile(user_id: str, display_name: str | None = None) -> dict[str, Any]:
    """Create a profile skeleton for one Jarvis user."""

    return {
        "id": user_id,
        "display_name": display_name or user_id,
        "settings": dict(DEFAULT_SETTINGS),
        "memory": {"preferences": {}, "notes": [], "habits": {}},
    }


def merge_user_profile(profile: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    """Merge settings while keeping the profile and memory isolated."""

    updated = copy.deepcopy(profile)
    updated.setdefault("settings", {}).update({key: value for key, value in settings.items() if key in DEFAULT_SETTINGS})
    return updated
