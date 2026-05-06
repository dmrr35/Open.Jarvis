"""Security helpers for future JARVIS plugins."""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path

from open_jarvis.plugins.manifest import validate_plugin_manifest_schema

TRUST_POLICY_FILE = Path(__file__).resolve().parent / "jarvis_plugin_trust.json"
DEFAULT_SANDBOX_POLICY = {
    "execution": "isolated",
    "timeout_seconds": 30,
    "network": "restricted",
    "filesystem": "scoped",
    "process_spawn": False,
    "max_memory_mb": 256,
}

REQUIRED_MANIFEST_KEYS = {"name", "version", "entrypoint", "signer"}


def load_plugin_trust_policy() -> dict:
    """Load the local plugin trust policy, falling back to defaults."""

    if TRUST_POLICY_FILE.exists():
        try:
            with open(TRUST_POLICY_FILE, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, JSONDecodeError):
            return {
                "trusted_signers": ["ci"],
                "trusted_plugins": [],
                "sandbox": build_plugin_sandbox_policy(),
            }
    return {
        "trusted_signers": ["ci"],
        "trusted_plugins": [],
        "sandbox": build_plugin_sandbox_policy(),
    }


def build_plugin_sandbox_policy() -> dict:
    """Return a conservative sandbox policy for plugins."""

    return dict(DEFAULT_SANDBOX_POLICY)


def validate_plugin_manifest(manifest: dict, trusted_signers: list[str] | None = None) -> dict:
    """Validate a plugin manifest and report trust issues.

    This keeps the legacy public API while delegating v0.3.0 manifest and
    permission checks to the normalized schema validator.
    """

    trust_policy = load_plugin_trust_policy()
    trusted_signers = trusted_signers or trust_policy.get("trusted_signers", ["ci"])
    policy = build_plugin_sandbox_policy()
    schema = validate_plugin_manifest_schema(manifest, allow_legacy=True)
    issues: list[str] = list(schema["issues"])
    warnings: list[str] = list(schema["warnings"])

    missing = sorted(REQUIRED_MANIFEST_KEYS - set(manifest))
    if missing:
        issues.append(f"missing required fields: {', '.join(missing)}")

    signer = str(manifest.get("signer", "")).strip()
    if signer not in trusted_signers:
        issues.append(f"signer '{signer or 'unset'}' is not trusted")

    name = str(manifest.get("name", "")).strip()
    if not name:
        issues.append("plugin name is empty")

    entrypoint = str(manifest.get("entrypoint", "")).strip()
    if entrypoint and Path(entrypoint).suffix != ".py":
        issues.append("entrypoint should point to a Python module")
    if entrypoint:
        entrypoint_path = Path(entrypoint)
        if entrypoint_path.is_absolute() or ".." in entrypoint_path.parts:
            issues.append("entrypoint must stay inside the plugin directory")

    actions = manifest.get("actions", [])
    if actions and not isinstance(actions, list):
        issues.append("actions must be a list")

    valid = not issues
    if valid and manifest.get("trusted") is False:
        issues.append("plugin is explicitly marked untrusted")
        valid = False

    return {
        "valid": valid,
        "issues": issues,
        "warnings": warnings,
        "policy": policy,
        "manifest": dict(schema["manifest"]),
        "id": schema["id"],
        "permissions": list(schema["permissions"]),
        "risk": schema["risk"],
        "legacy": schema["legacy"],
        "trust_policy": trust_policy,
    }


def build_plugin_trust_summary(manifests: list[dict], trusted_signers: list[str] | None = None) -> dict:
    """Summarize plugin trust posture across multiple manifests."""

    trusted_signers = trusted_signers or ["ci"]
    results = [validate_plugin_manifest(manifest, trusted_signers=trusted_signers) for manifest in manifests]
    valid_count = sum(1 for item in results if item["valid"])
    return {
        "valid_count": valid_count,
        "invalid_count": len(results) - valid_count,
        "results": results,
        "policy": build_plugin_sandbox_policy(),
    }
