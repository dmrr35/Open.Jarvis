"""User-visible security and permission overview helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from permission_profiles import build_permission_matrix, get_active_permission_profile
from privacy_mode import build_privacy_session
from runtime_safety import requires_confirmation

DEFAULT_SECRET_KEYS = ("GROQ_API_KEY", "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "GEMINI_API_KEY", "JARVIS_LOCAL_LLM_URL")


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _secret_status(env: Mapping[str, str], keys: Sequence[str]) -> dict[str, str]:
    return {key: "CONFIGURED" if str(env.get(key, "")).strip() else "MISSING" for key in keys}


def build_security_overview(
    env: Mapping[str, str],
    *,
    actions: Sequence[str] = ("open_web", "shutdown", "restart", "sleep", "lock_screen", "type_text", "press_key", "mouse_click"),
    secret_keys: Sequence[str] = DEFAULT_SECRET_KEYS,
) -> dict:
    """Build a compact security summary for the UI and docs."""

    action_list = list(actions)
    return {
        "profile": get_active_permission_profile(env),
        "privacy": build_privacy_session(enabled=_truthy(env.get("JARVIS_PRIVACY_MODE"))),
        "secrets": _secret_status(env, secret_keys),
        "permission_matrix": build_permission_matrix(action_list),
        "confirmation_required": [action for action in action_list if requires_confirmation(action)],
    }
