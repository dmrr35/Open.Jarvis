"""Local plugin registry discovery without executing plugin code."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from open_jarvis.plugins.manifest import validate_plugin_manifest_schema
from open_jarvis.plugins.plugin_state import build_plugin_state


def _read_manifest(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, JSONDecodeError) as exc:
        return {"name": path.parent.name, "version": "unknown", "entrypoint": "", "permissions": []}, [f"manifest could not be read: {exc.__class__.__name__}"]


def discover_plugin_manifests(root: Path | str) -> list[dict[str, Any]]:
    """Return raw local manifest records without importing plugin code."""

    root_path = Path(root)
    records: list[dict[str, Any]] = []
    for manifest_path in sorted(root_path.glob("*/plugin.json")):
        manifest, read_issues = _read_manifest(manifest_path)
        records.append({"path": manifest_path, "plugin_dir": manifest_path.parent, "manifest": manifest, "read_issues": read_issues})
    return records


def build_plugin_registry(
    root: Path | str = "plugins",
    *,
    state_file: Path | str | None = None,
    permission_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build local plugin registry metadata with validation and enablement state."""

    state = build_plugin_state(state_file) if state_file else {"plugins": {}, "audit": []}
    records = discover_plugin_manifests(root)
    id_counts: dict[str, int] = {}
    entries: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for record in records:
        manifest_path = record["path"]
        plugin_dir = record["plugin_dir"]
        validation = validate_plugin_manifest_schema(record["manifest"], plugin_dir=plugin_dir, permission_policy=permission_policy)
        issues = list(record["read_issues"]) + list(validation["issues"])
        warnings = list(validation["warnings"])
        manifest = validation["manifest"]
        plugin_id = str(validation["id"] or manifest_path.parent.name)
        id_counts[plugin_id] = id_counts.get(plugin_id, 0) + 1
        state_record = state["plugins"].get(plugin_id) or state["plugins"].get(str(manifest.get("name", "")), {})
        enabled = bool(state_record.get("enabled", False))
        status = "blocked" if issues else "enabled" if enabled else "available"
        entries.append(
            {
                "id": plugin_id,
                "name": manifest.get("name", manifest_path.parent.name),
                "version": manifest.get("version", "unknown"),
                "description": manifest.get("description", ""),
                "path": str(plugin_dir),
                "manifest_path": str(manifest_path),
                "manifest": manifest,
                "permissions": list(validation["permissions"]),
                "risk": validation["risk"],
                "enabled": enabled and not issues,
                "status": status,
                "issues": issues,
                "warnings": warnings,
                "legacy": validation["legacy"],
            }
        )
        seen_paths.add(str(plugin_dir))

    duplicate_ids = {plugin_id for plugin_id, count in id_counts.items() if count > 1}
    if duplicate_ids:
        for entry in entries:
            if entry["id"] in duplicate_ids:
                entry["enabled"] = False
                entry["status"] = "blocked"
                entry["issues"].append(f"duplicate plugin id: {entry['id']}")

    for plugin_id, state_record in sorted(state["plugins"].items()):
        path = str(state_record.get("path", ""))
        if plugin_id not in id_counts and path not in seen_paths:
            entries.append(
                {
                    "id": plugin_id,
                    "name": plugin_id,
                    "version": str(state_record.get("version", "")),
                    "description": "",
                    "path": path,
                    "manifest_path": "",
                    "manifest": {},
                    "permissions": [],
                    "risk": "low",
                    "enabled": False,
                    "status": "missing",
                    "issues": ["enabled state exists but plugin manifest is missing"],
                    "warnings": [],
                    "legacy": False,
                }
            )

    entries.sort(key=lambda item: (item["status"] == "blocked", item["id"]))
    return {
        "plugins": entries,
        "summary": {
            "total": len(entries),
            "enabled": sum(1 for item in entries if item["status"] == "enabled"),
            "available": sum(1 for item in entries if item["status"] == "available"),
            "blocked": sum(1 for item in entries if item["status"] == "blocked"),
            "missing": sum(1 for item in entries if item["status"] == "missing"),
        },
    }
