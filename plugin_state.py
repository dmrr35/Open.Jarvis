"""Persistent enable/disable state for local plugins."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from plugin_signature import verify_plugin_signature

DEFAULT_STATE_FILE = Path(__file__).resolve().parent / "jarvis_plugin_state.json"


def build_plugin_state(state_file: Path | str = DEFAULT_STATE_FILE) -> dict[str, Any]:
    """Load plugin enablement state from disk."""

    path = Path(state_file)
    if not path.exists():
        return {"plugins": {}, "audit": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, JSONDecodeError):
        return {"plugins": {}, "audit": []}
    plugins = data.get("plugins", {})
    audit = data.get("audit", [])
    return {
        "plugins": plugins if isinstance(plugins, dict) else {},
        "audit": audit if isinstance(audit, list) else [],
    }


def _write_plugin_state(state: dict[str, Any], state_file: Path | str) -> None:
    path = Path(state_file)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def enable_plugin(
    plugin_name: str,
    manifest: dict[str, Any],
    *,
    state_file: Path | str = DEFAULT_STATE_FILE,
    signing_keys: dict[str, str] | None = None,
    approved_by: str = "local-user",
    approval_reason: str = "manual approval",
) -> dict[str, Any]:
    """Enable a plugin only when its signature verifies."""

    verification = verify_plugin_signature(manifest, signing_keys=signing_keys)
    if not verification["valid"]:
        return {"status": "blocked", "plugin": plugin_name, "verification": verification}

    state = build_plugin_state(state_file)
    state["plugins"][plugin_name] = {
        "enabled": True,
        "signer": manifest.get("signer", ""),
        "version": manifest.get("version", ""),
        "signature": manifest.get("signature", ""),
        "approved_by": approved_by,
        "approval_reason": approval_reason,
    }
    approval = {"approved_by": approved_by, "reason": approval_reason}
    state["audit"].append({"plugin": plugin_name, "action": "enable", **approval})
    _write_plugin_state(state, state_file)
    return {"status": "enabled", "plugin": plugin_name, "verification": verification, "approval": approval}


def disable_plugin(
    plugin_name: str,
    *,
    state_file: Path | str = DEFAULT_STATE_FILE,
    approved_by: str = "local-user",
    approval_reason: str = "manual disable",
) -> dict[str, Any]:
    """Disable a plugin while keeping an audit-friendly state record."""

    state = build_plugin_state(state_file)
    current = state["plugins"].get(plugin_name, {})
    state["plugins"][plugin_name] = {
        **current,
        "enabled": False,
        "approved_by": approved_by,
        "approval_reason": approval_reason,
    }
    state["audit"].append({"plugin": plugin_name, "action": "disable", "approved_by": approved_by, "reason": approval_reason})
    _write_plugin_state(state, state_file)
    return {"status": "disabled", "plugin": plugin_name}


def plugin_enabled(plugin_name: str, *, state_file: Path | str = DEFAULT_STATE_FILE) -> bool:
    """Return whether a plugin is currently enabled."""

    state = build_plugin_state(state_file)
    return bool(state["plugins"].get(plugin_name, {}).get("enabled"))


def build_plugin_state_audit(state_file: Path | str = DEFAULT_STATE_FILE) -> dict[str, Any]:
    """Return plugin state audit events in write order."""

    state = build_plugin_state(state_file)
    return {"events": list(state["audit"]), "total": len(state["audit"])}
