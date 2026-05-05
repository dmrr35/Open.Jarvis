"""Release signing policy and verification helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import date
from json import JSONDecodeError
from pathlib import Path
from typing import Any

POLICY_FILE = Path(__file__).resolve().parent / "release_security.json"
DEFAULT_POLICY: dict[str, Any] = {
    "require_signature": True,
    "signature_algorithm": "hmac-sha256",
    "trusted_signers": ["ci"],
    "key_policy": {
        "env_var": "JARVIS_RELEASE_SIGNING_KEY",
        "min_length": 16,
        "rotation_days": 90,
    },
}


def load_release_policy() -> dict[str, Any]:
    """Load release policy from disk or fall back to defaults."""

    if POLICY_FILE.exists():
        try:
            with open(POLICY_FILE, encoding="utf-8") as handle:
                policy = json.load(handle)
                return _normalize_policy(policy)
        except (OSError, JSONDecodeError):
            return _normalize_policy(DEFAULT_POLICY)
    return _normalize_policy(DEFAULT_POLICY)


def _normalize_policy(policy: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(DEFAULT_POLICY)
    result.update(policy or {})
    key_policy = dict(DEFAULT_POLICY["key_policy"])
    loaded_key_policy = result.get("key_policy", {})
    if isinstance(loaded_key_policy, dict):
        key_policy.update(loaded_key_policy)
    result["key_policy"] = key_policy
    trusted_signers = result.get("trusted_signers", ["ci"])
    result["trusted_signers"] = list(trusted_signers) if isinstance(trusted_signers, list) else ["ci"]
    return result


def _signing_key() -> str:
    policy = load_release_policy()
    env_var = policy["key_policy"]["env_var"]
    env_value = os.getenv(env_var, "")
    if env_value:
        return env_value
    if POLICY_FILE.with_name(".env").exists():
        for raw_line in POLICY_FILE.with_name(".env").read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == env_var:
                return value.strip()
    return ""


def build_release_manifest(version: str, artifact: dict, signer: str = "ci") -> dict:
    """Build the deterministic manifest that CI signs and publishes with artifacts."""

    return {
        "schema_version": 1,
        "version": version,
        "artifact": dict(artifact),
        "signer": signer,
        "signature_algorithm": load_release_policy()["signature_algorithm"],
    }


def validate_release_environment(env: dict[str, str] | None = None, trusted_signers: list[str] | None = None) -> dict:
    """Validate release signing inputs without reading or printing secret values."""

    env = env or {}
    policy = load_release_policy()
    key_policy = policy["key_policy"]
    key = str(env.get(key_policy["env_var"], os.getenv(key_policy["env_var"], ""))).strip()
    signers = trusted_signers or policy.get("trusted_signers", ["ci"])
    checks = [
        {
            "id": "signing_key",
            "status": "ready" if not _validate_key_policy(key, key_policy) else "missing",
            "detail": f"{key_policy['env_var']} is configured." if key else f"{key_policy['env_var']} is missing.",
        },
        {
            "id": "trusted_signers",
            "status": "ready" if signers else "missing",
            "detail": f"Trusted signers: {', '.join(signers)}." if signers else "No trusted signers are configured.",
        },
        {
            "id": "signature_required",
            "status": "ready" if policy.get("require_signature") else "missing",
            "detail": "Release signatures are required." if policy.get("require_signature") else "Release signatures are optional.",
        },
    ]
    return {"ready": all(check["status"] == "ready" for check in checks), "checks": checks, "policy": policy}


def build_key_rotation_plan(last_rotated: str | None, today: str | None = None, rotation_days: int | None = None) -> dict:
    """Return a release-key rotation status from ISO dates."""

    policy = load_release_policy()["key_policy"]
    rotation_days = int(rotation_days or policy.get("rotation_days", 90))
    current = date.fromisoformat(today) if today else date.today()
    if not last_rotated:
        return {"status": "missing", "days_remaining": 0, "action": "Record the last signing-key rotation date."}
    rotated_at = date.fromisoformat(last_rotated)
    age_days = (current - rotated_at).days
    days_remaining = max(rotation_days - age_days, 0)
    status = "rotate_now" if age_days >= rotation_days else "rotate_soon" if days_remaining <= 14 else "current"
    actions = {
        "current": "No key rotation needed yet.",
        "rotate_soon": "Schedule release signing key rotation soon.",
        "rotate_now": "Rotate the release signing key before the next release.",
    }
    return {
        "status": status,
        "age_days": age_days,
        "days_remaining": days_remaining,
        "rotation_days": rotation_days,
        "action": actions[status],
    }


def _validate_key_policy(key: str, policy: dict) -> str | None:
    if not key:
        return f"Missing signing key in {policy['env_var']}"
    if len(key) < int(policy.get("min_length", 16)):
        return "Signing key is shorter than the minimum policy length"
    return None


def sign_release_payload(payload: dict, signer: str = "ci") -> str:
    """Create an HMAC signature for a release payload."""

    key = _signing_key()
    policy = load_release_policy()["key_policy"]
    validation_error = _validate_key_policy(key, policy)
    if validation_error:
        raise ValueError(validation_error)

    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(key.encode("utf-8"), serialized + b"|" + signer.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_release_signature(payload: dict, signature: str, signer: str = "ci", trusted_signers: list[str] | None = None) -> dict:
    """Verify that a payload signature is valid and the signer is trusted."""

    policy = load_release_policy()
    trusted_signers = trusted_signers or policy.get("trusted_signers", ["ci"])
    if signer not in trusted_signers:
        return {"valid": False, "reason": "untrusted signer"}

    key = _signing_key()
    key_error = _validate_key_policy(key, policy["key_policy"])
    if key_error:
        return {"valid": False, "reason": key_error}

    expected = sign_release_payload(payload, signer=signer)
    return {
        "valid": hmac.compare_digest(expected, signature),
        "reason": "signature matched" if hmac.compare_digest(expected, signature) else "signature mismatch",
    }


def build_release_smoke_check(version: str, artifact: dict, signer: str = "ci") -> dict:
    """Generate a deterministic signing smoke check for CI."""

    payload = {"version": version, "artifact": artifact}
    signature = sign_release_payload(payload, signer=signer)
    verification = verify_release_signature(payload, signature, signer=signer)
    return {
        "payload": payload,
        "signature": signature,
        "verification": verification,
        "policy": load_release_policy(),
    }
