"""Manifest normalization and validation for local JARVIS plugins."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from open_jarvis.plugins.permissions import validate_plugin_permissions

PLUGIN_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")
NEW_REQUIRED_FIELDS = {"id", "name", "version", "entrypoint", "permissions"}
LEGACY_REQUIRED_FIELDS = {"name", "version", "entrypoint"}


def derive_plugin_id(name: str) -> str:
    """Derive a stable-ish plugin id from a display name for legacy manifests."""

    lowered = name.strip().lower()
    normalized = re.sub(r"[^a-z0-9_-]+", "_", lowered)
    normalized = re.sub(r"_+", "_", normalized).strip("_-")
    if not normalized or not normalized[0].isalpha():
        normalized = f"plugin_{normalized}" if normalized else "plugin"
    return normalized[:64]


def _entrypoint_is_safe(entrypoint: str, plugin_dir: Path | None = None) -> bool:
    path = Path(entrypoint)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".py":
        return False
    if plugin_dir is None:
        return True
    root = plugin_dir.resolve()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def validate_plugin_manifest_schema(
    manifest: dict[str, Any],
    *,
    plugin_dir: Path | str | None = None,
    allow_legacy: bool = True,
    permission_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and normalize a plugin manifest without importing plugin code."""

    issues: list[str] = []
    warnings: list[str] = []
    plugin_dir_path = Path(plugin_dir) if plugin_dir is not None else None
    if not isinstance(manifest, dict):
        return {
            "valid": False,
            "issues": ["manifest must be an object"],
            "warnings": [],
            "manifest": {},
            "id": "",
            "permissions": [],
            "risk": "critical",
            "legacy": False,
        }

    normalized = dict(manifest)
    legacy = False
    missing_new = sorted(NEW_REQUIRED_FIELDS - set(manifest))
    if missing_new:
        legacy_candidate = allow_legacy and LEGACY_REQUIRED_FIELDS.issubset(manifest)
        if legacy_candidate:
            legacy = True
            if "id" not in normalized:
                normalized["id"] = derive_plugin_id(str(normalized.get("name", "")))
                warnings.append("manifest id is missing; derived from name")
            if "permissions" not in normalized:
                normalized["permissions"] = []
                warnings.append("manifest permissions are missing; defaulted to empty permissions")
        else:
            issues.append(f"missing required fields: {', '.join(missing_new)}")

    plugin_id = str(normalized.get("id", "")).strip()
    if plugin_id and not PLUGIN_ID_RE.match(plugin_id):
        issues.append("plugin id must match ^[a-z][a-z0-9_-]{2,63}$")
    if not str(normalized.get("name", "")).strip():
        issues.append("plugin name is empty")
    if not str(normalized.get("version", "")).strip():
        issues.append("plugin version is empty")

    entrypoint = str(normalized.get("entrypoint", "")).strip()
    if not entrypoint:
        issues.append("plugin entrypoint is empty")
    elif not _entrypoint_is_safe(entrypoint, plugin_dir_path):
        issues.append("entrypoint must be a relative Python file inside the plugin directory")

    permissions_result = validate_plugin_permissions(normalized.get("permissions", []), policy=permission_policy)
    if not permissions_result["valid"]:
        issues.extend(permissions_result["issues"])
    warnings.extend(permissions_result["warnings"])
    normalized["permissions"] = permissions_result["permissions"]

    requires = normalized.get("requires", {})
    if requires and not isinstance(requires, dict):
        issues.append("requires must be an object")
    enabled_by_default = normalized.get("enabled_by_default", False)
    if not isinstance(enabled_by_default, bool):
        issues.append("enabled_by_default must be a boolean")

    return {
        "valid": not issues,
        "issues": issues,
        "warnings": warnings,
        "manifest": normalized,
        "id": plugin_id or str(normalized.get("id", "")),
        "permissions": normalized.get("permissions", []),
        "risk": permissions_result["risk"],
        "blocked_permissions": permissions_result["blocked_permissions"],
        "legacy": legacy,
    }
