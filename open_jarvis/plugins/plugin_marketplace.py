"""Local plugin marketplace listing and trust scoring."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path

from open_jarvis.plugins.plugin_runner import build_plugin_execution_plan
from open_jarvis.plugins.plugin_security import validate_plugin_manifest
from open_jarvis.plugins.plugin_signature import verify_plugin_signature
from open_jarvis.plugins.plugin_state import build_plugin_state


def _read_manifest(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, JSONDecodeError):
        return {"name": path.parent.name, "version": "unknown", "entrypoint": "", "signer": ""}


def build_marketplace(
    root: Path | str,
    trusted_signers: list[str] | None = None,
    signing_keys: dict[str, str] | None = None,
    state_file: Path | str | None = None,
) -> dict:
    """Scan local plugin manifests and return sorted trust metadata."""

    root = Path(root)
    state = build_plugin_state(state_file) if state_file else {"plugins": {}}
    plugins = []
    for manifest_path in sorted(root.glob("*/plugin.json")):
        manifest = _read_manifest(manifest_path)
        validation = validate_plugin_manifest(manifest, trusted_signers=trusted_signers)
        signature = verify_plugin_signature(manifest, signing_keys=signing_keys)
        issues = list(validation["issues"])
        if not signature["valid"]:
            issues.append(signature["reason"])
        name = str(manifest.get("name", manifest_path.parent.name))
        enabled = bool(state["plugins"].get(name, {}).get("enabled"))
        execution_plan = build_plugin_execution_plan(
            manifest_path.parent, manifest, trusted_signers=trusted_signers, signing_keys=signing_keys
        )
        sandbox_status = "ready" if execution_plan["status"] == "ready" else "blocked"
        approval_action = {
            "action": "disable" if enabled else "enable",
            "label": f"{'Disable' if enabled else 'Enable'} {name}",
            "requires_signature": True,
            "requires_sandbox": True,
        }
        if sandbox_status != "ready" or issues:
            approval_action = {
                "action": "blocked",
                "label": f"{name} is blocked",
                "requires_signature": True,
                "requires_sandbox": True,
            }
        plugins.append(
            {
                "id": manifest.get("id", validation.get("id", name)),
                "name": name,
                "version": manifest.get("version", "unknown"),
                "description": manifest.get("description", ""),
                "path": str(manifest_path.parent),
                "trust_status": "trusted" if validation["valid"] and signature["valid"] else "blocked",
                "signature_status": signature["status"],
                "sandbox_status": sandbox_status,
                "approval_action": approval_action,
                "enabled": enabled,
                "permissions": list(validation.get("permissions", [])),
                "risk": validation.get("risk", "low"),
                "warnings": list(validation.get("warnings", [])),
                "issues": issues,
            }
        )

    plugins.sort(key=lambda item: (item["trust_status"] != "trusted", item["name"]))
    return {
        "plugins": plugins,
        "summary": {
            "total": len(plugins),
            "trusted": sum(1 for item in plugins if item["trust_status"] == "trusted"),
            "blocked": sum(1 for item in plugins if item["trust_status"] == "blocked"),
        },
    }
