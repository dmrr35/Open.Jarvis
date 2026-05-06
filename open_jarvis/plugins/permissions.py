"""Permission registry and validation for local JARVIS plugins."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass(frozen=True)
class PluginPermission:
    """Metadata for one plugin permission."""

    name: str
    risk: str
    description: str


PERMISSION_REGISTRY: dict[str, PluginPermission] = {
    "commands.register": PluginPermission("commands.register", "low", "Register plugin command metadata."),
    "commands.execute": PluginPermission("commands.execute", "high", "Request command execution through JARVIS safety gates."),
    "ui.notify": PluginPermission("ui.notify", "low", "Emit user-visible notifications or command-stream events."),
    "memory.read": PluginPermission("memory.read", "medium", "Read scoped assistant memory through an adapter."),
    "memory.write": PluginPermission("memory.write", "medium", "Write scoped assistant memory through an adapter."),
    "audio.play": PluginPermission("audio.play", "medium", "Request audio playback through an approved adapter."),
    "network.request": PluginPermission("network.request", "high", "Request outbound network access through an approved adapter."),
    "filesystem.read": PluginPermission("filesystem.read", "high", "Read files inside an approved scoped path."),
    "filesystem.write": PluginPermission("filesystem.write", "critical", "Write files inside an approved scoped path."),
    "spotify.control": PluginPermission("spotify.control", "medium", "Request Spotify controls when the integration is configured."),
    "groq.request": PluginPermission("groq.request", "medium", "Request Groq-backed provider calls through a safe adapter."),
    "desktop.automation": PluginPermission("desktop.automation", "critical", "Request desktop automation such as keyboard or mouse actions."),
    "process.spawn": PluginPermission("process.spawn", "critical", "Spawn child processes from plugin code."),
}


def list_plugin_permissions() -> list[dict[str, str]]:
    """Return registered permissions in deterministic order."""

    return [
        {"name": permission.name, "risk": permission.risk, "description": permission.description}
        for permission in sorted(PERMISSION_REGISTRY.values(), key=lambda item: item.name)
    ]


def permission_known(permission: str) -> bool:
    """Return whether a permission exists in the registry."""

    return permission in PERMISSION_REGISTRY


def permission_risk(permission: str) -> str:
    """Return the risk level for a known permission, or critical for unknown values."""

    definition = PERMISSION_REGISTRY.get(permission)
    return definition.risk if definition else "critical"


def highest_permission_risk(permissions: list[str]) -> str:
    """Return the highest risk level represented by a permission list."""

    highest = "low"
    for permission in permissions:
        risk = permission_risk(permission)
        if RISK_ORDER[risk] > RISK_ORDER[highest]:
            highest = risk
    return highest


def validate_plugin_permissions(permissions: Any, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate requested plugin permissions with deny-by-default risky behavior."""

    policy = dict(policy or {})
    approved_permissions = set(policy.get("approved_permissions", []))
    allow_high_risk = bool(policy.get("allow_high_risk", False))
    allow_critical = bool(policy.get("allow_critical", False))
    issues: list[str] = []
    warnings: list[str] = []
    normalized: list[str] = []
    blocked: list[str] = []

    if not isinstance(permissions, list):
        return {
            "valid": False,
            "issues": ["permissions must be a list"],
            "warnings": [],
            "permissions": [],
            "blocked_permissions": [],
            "risk": "critical",
        }

    seen: set[str] = set()
    for raw_permission in permissions:
        if not isinstance(raw_permission, str) or not raw_permission.strip():
            issues.append("permissions must contain non-empty strings")
            continue
        permission = raw_permission.strip()
        if permission in seen:
            issues.append(f"duplicate permission: {permission}")
            continue
        seen.add(permission)
        normalized.append(permission)

        if permission not in PERMISSION_REGISTRY:
            issues.append(f"unknown permission: {permission}")
            blocked.append(permission)
            continue

        risk = permission_risk(permission)
        approved = permission in approved_permissions
        if risk == "high" and not (allow_high_risk or approved):
            issues.append(f"high-risk permission requires explicit approval: {permission}")
            blocked.append(permission)
        if risk == "critical" and not (allow_critical or approved):
            issues.append(f"critical permission is blocked by default: {permission}")
            blocked.append(permission)
        if risk in {"high", "critical"} and approved:
            warnings.append(f"risky permission explicitly approved: {permission}")

    return {
        "valid": not issues,
        "issues": issues,
        "warnings": warnings,
        "permissions": normalized,
        "blocked_permissions": blocked,
        "risk": highest_permission_risk(normalized) if normalized else "low",
    }


def require_plugin_permission(permission: str, granted_permissions: list[str]) -> None:
    """Raise a permission error when a plugin lacks a required permission."""

    from open_jarvis.plugins.errors import PluginPermissionError

    if permission not in granted_permissions:
        raise PluginPermissionError(
            f"Plugin permission required: {permission}",
            issues=[f"missing permission: {permission}"],
            detail={"permission": permission},
        )
