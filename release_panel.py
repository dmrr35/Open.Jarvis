"""Release readiness panel helpers."""

from __future__ import annotations

from collections.abc import Mapping

from release_security import load_release_policy


def build_release_panel(env: Mapping[str, str] | None = None, trusted_signers: list[str] | None = None) -> dict:
    """Report signing readiness for CI and local release screens."""

    env = env or {}
    policy = load_release_policy()
    key_policy = policy["key_policy"]
    key = str(env.get(key_policy["env_var"], "")).strip()
    signers = trusted_signers or policy.get("trusted_signers", ["ci"])
    checks = [
        {
            "id": "signing_key",
            "status": "ready" if len(key) >= int(key_policy.get("min_length", 16)) else "missing",
            "fix": f"Set {key_policy['env_var']} with at least {key_policy.get('min_length', 16)} characters.",
        },
        {
            "id": "trusted_signers",
            "status": "ready" if signers else "missing",
            "fix": "Add at least one trusted signer.",
        },
    ]
    return {"ready": all(check["status"] == "ready" for check in checks), "checks": checks, "trusted_signers": signers}
