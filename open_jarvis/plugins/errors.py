"""Typed plugin errors for diagnostics without leaking sensitive details."""

from __future__ import annotations

from typing import Any


class PluginError(Exception):
    """Base class for plugin-system failures."""

    def __init__(self, message: str, *, plugin_id: str = "", issues: list[str] | None = None, detail: dict[str, Any] | None = None):
        super().__init__(message)
        self.plugin_id = plugin_id
        self.issues = list(issues or [])
        self.detail = dict(detail or {})

    def as_diagnostic(self) -> dict[str, Any]:
        """Return a structured, user-safe diagnostic payload."""

        return {
            "type": self.__class__.__name__,
            "plugin_id": self.plugin_id,
            "message": str(self),
            "issues": list(self.issues),
            "detail": dict(self.detail),
        }


class PluginManifestError(PluginError):
    """Raised when a plugin manifest is malformed or unsafe."""


class PluginPermissionError(PluginError):
    """Raised when a plugin requests or uses a permission it does not have."""


class PluginLoadError(PluginError):
    """Raised when a plugin cannot be imported or prepared."""


class PluginRuntimeError(PluginError):
    """Raised when a plugin hook fails at runtime."""
