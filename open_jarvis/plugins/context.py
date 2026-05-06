"""Safe context object exposed to local JARVIS plugins."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from open_jarvis.memory.privacy_mode import mask_sensitive_text, mask_sensitive_value
from open_jarvis.plugins.errors import PluginPermissionError
from open_jarvis.plugins.permissions import require_plugin_permission


@dataclass
class PluginContext:
    """Small permission-gated facade for plugin hooks."""

    plugin_id: str
    plugin_dir: Path
    permissions: list[str]
    notifications: list[dict[str, str]] = field(default_factory=list)
    commands: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    logger: Any = None

    def has_permission(self, permission: str) -> bool:
        """Return whether this plugin has a permission in its manifest."""

        return permission in self.permissions

    def require_permission(self, permission: str) -> None:
        """Raise when the plugin lacks a required permission."""

        try:
            require_plugin_permission(permission, self.permissions)
        except PluginPermissionError as exc:
            exc.plugin_id = self.plugin_id
            raise

    def notify(self, message: str, level: str = "info") -> dict[str, str]:
        """Record a safe user-facing notification."""

        self.require_permission("ui.notify")
        safe_message = mask_sensitive_text(str(message))
        notification = {"plugin_id": self.plugin_id, "level": str(level), "message": safe_message}
        self.notifications.append(notification)
        if self.logger is not None:
            log_method = getattr(self.logger, "warning" if level == "warning" else "info", None)
            if callable(log_method):
                log_method("[plugin:%s] %s", self.plugin_id, safe_message)
        return notification

    def register_command(self, name: str, metadata: dict[str, Any] | None = None, handler: Callable[..., Any] | None = None) -> dict[str, Any]:
        """Register command metadata without exposing the raw command dispatcher."""

        self.require_permission("commands.register")
        command_name = str(name).strip()
        if not command_name:
            raise ValueError("command name cannot be empty")
        payload = {"name": command_name, "metadata": mask_sensitive_value(metadata or {}), "handler": handler}
        self.commands[command_name] = payload
        return {"plugin_id": self.plugin_id, "name": command_name, "metadata": payload["metadata"]}

    def emit_event(self, event_type: str, detail: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record a safe plugin diagnostic event."""

        event = {
            "plugin_id": self.plugin_id,
            "event_type": str(event_type),
            "detail": mask_sensitive_text(str(detail)),
            "context": mask_sensitive_value(context or {}),
        }
        self.events.append(event)
        return event

    def request_memory_read(self, scope: str = "default") -> dict[str, Any]:
        """Deny-by-default memory read facade until a real adapter is provided."""

        self.require_permission("memory.read")
        return {"status": "unavailable", "scope": str(scope), "reason": "memory adapter is not configured"}

    def request_memory_write(self, scope: str, value: Any) -> dict[str, Any]:
        """Deny-by-default memory write facade until a real adapter is provided."""

        self.require_permission("memory.write")
        return {"status": "unavailable", "scope": str(scope), "value": mask_sensitive_value(value), "reason": "memory adapter is not configured"}

    def request_filesystem_read(self, relative_path: str) -> dict[str, Any]:
        """Deny-by-default filesystem read facade."""

        self.require_permission("filesystem.read")
        return {"status": "blocked", "path": str(relative_path), "reason": "filesystem adapter is not configured"}

    def request_filesystem_write(self, relative_path: str, content: str) -> dict[str, Any]:
        """Deny-by-default filesystem write facade."""

        self.require_permission("filesystem.write")
        return {"status": "blocked", "path": str(relative_path), "bytes": len(str(content)), "reason": "filesystem adapter is not configured"}

    def request_provider(self, provider_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Deny-by-default provider facade for cloud/local model requests."""

        permission = "groq.request" if provider_id == "groq" else "network.request"
        self.require_permission(permission)
        return {"status": "unavailable", "provider": provider_id, "payload": mask_sensitive_value(payload), "reason": "provider adapter is not configured"}


def build_plugin_context(
    plugin_id: str,
    plugin_dir: Path | str,
    permissions: list[str] | None = None,
    *,
    logger: Any = None,
) -> PluginContext:
    """Build a safe plugin context."""

    return PluginContext(plugin_id=plugin_id, plugin_dir=Path(plugin_dir), permissions=list(permissions or []), logger=logger)
