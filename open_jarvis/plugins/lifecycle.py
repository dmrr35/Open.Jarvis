"""Plugin lifecycle hook helpers."""

from __future__ import annotations

from typing import Any

LIFECYCLE_HOOKS = ("on_load", "on_enable", "on_disable", "on_command", "on_shutdown")


def available_hooks(module: Any) -> list[str]:
    """Return lifecycle hooks implemented by a plugin module."""

    return [hook for hook in LIFECYCLE_HOOKS if callable(getattr(module, hook, None))]


def build_hook_result(plugin_id: str, hook: str, status: str, error: str = "") -> dict[str, str]:
    """Return a stable hook result payload."""

    return {"plugin_id": plugin_id, "hook": hook, "status": status, "error": error}
