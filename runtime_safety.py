"""Safety gates for high-impact runtime actions."""

from __future__ import annotations

import os
from collections.abc import Mapping

DESTRUCTIVE_ACTIONS = {"shutdown", "restart", "sleep", "lock_screen"}
CONFIRMATION_ACTIONS = DESTRUCTIVE_ACTIONS | {"type_text", "press_key", "mouse_click", "scroll", "close_window"}


def is_destructive_action(action: str) -> bool:
    """Return whether an action can disrupt the active desktop session."""

    return action in DESTRUCTIVE_ACTIONS


def requires_confirmation(action: str) -> bool:
    """Return whether an action should get explicit user approval in the UI."""

    return action in CONFIRMATION_ACTIONS


def build_confirmation_prompt(action: str, params: dict | None = None) -> str:
    """Build a concise approval prompt for sensitive actions."""

    detail = f"\nParameters: {params}" if params else ""
    return (
        "Jarvis wants to run a sensitive action.\n"
        f"Action: {action}{detail}\n"
        "Approve or cancel before continuing."
    )


def is_destructive_action_allowed(env: Mapping[str, str] | None = None) -> bool:
    """Allow destructive desktop actions only when explicitly enabled."""

    env = os.environ if env is None else env
    return env.get("JARVIS_ALLOW_DESTRUCTIVE_ACTIONS", "").strip().lower() in {"1", "true", "yes", "on"}


def block_message(action: str) -> str:
    """Return an actionable user-facing safety message."""

    return (
        f"I blocked the {action} action, sir.\n"
        "Reason: it can interrupt or terminate the current desktop session.\n"
        "Fix: set JARVIS_ALLOW_DESTRUCTIVE_ACTIONS=true only when you intentionally want Jarvis to run it."
    )
