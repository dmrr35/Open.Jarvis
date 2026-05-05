"""Permission profiles for runtime command safety."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from runtime_safety import is_destructive_action

PROFILES: dict[str, dict[str, Any]] = {
    "safe": {
        "allow_destructive": False,
        "allowed_actions": {"talk", "open_web", "google_search", "remember", "recall", "spotify_play", "spotify_pause"},
    },
    "normal": {
        "allow_destructive": False,
        "allowed_actions": {"*"},
    },
    "admin": {
        "allow_destructive": True,
        "allowed_actions": {"*"},
    },
}


def action_allowed(action: str, profile: str = "normal") -> bool:
    """Return whether a profile may execute an action."""

    config = PROFILES.get(profile, PROFILES["normal"])
    if is_destructive_action(action) and not config["allow_destructive"]:
        return False
    allowed = config["allowed_actions"]
    return "*" in allowed or action in allowed


def get_active_permission_profile(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Return the currently selected permission profile with a safe fallback."""

    env = os.environ if env is None else env
    profile_id = str(env.get("JARVIS_PERMISSION_PROFILE", "normal")).strip().lower() or "normal"
    if profile_id not in PROFILES:
        profile_id = "normal"
    config = PROFILES[profile_id]
    return {
        "id": profile_id,
        "label": profile_id.upper(),
        "allow_destructive": bool(config["allow_destructive"]),
        "allowed_actions": sorted(config["allowed_actions"]),
    }


def build_permission_matrix(actions: list[str]) -> dict[str, dict[str, str]]:
    """Render actions across all profiles for settings screens."""

    return {action: {profile: "allowed" if action_allowed(action, profile) else "blocked" for profile in PROFILES} for action in actions}
