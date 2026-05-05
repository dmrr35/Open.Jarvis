"""Plugin manifest signing and verification helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from collections.abc import Mapping
from typing import Any

SIGNATURE_FIELD = "signature"


def _canonical_manifest(manifest: dict[str, Any]) -> bytes:
    """Serialize a manifest deterministically without the mutable signature."""

    unsigned = {key: value for key, value in manifest.items() if key != SIGNATURE_FIELD}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sign_plugin_manifest(manifest: dict[str, Any], signing_key: str) -> dict[str, Any]:
    """Return a signed manifest without mutating the caller's input."""

    signature = hmac.new(signing_key.encode("utf-8"), _canonical_manifest(manifest), hashlib.sha256).hexdigest()
    signed_manifest = dict(manifest)
    signed_manifest[SIGNATURE_FIELD] = signature
    return {"signature": signature, "manifest": signed_manifest}


def load_plugin_signing_keys(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Load local plugin signing keys without exposing secret values."""

    source = env if env is not None else os.environ
    keys: dict[str, str] = {}
    ci_key = source.get("JARVIS_PLUGIN_SIGNING_KEY", "").strip()
    if ci_key:
        keys["ci"] = ci_key

    raw_keys = source.get("JARVIS_PLUGIN_SIGNING_KEYS", "").strip()
    if raw_keys:
        try:
            parsed = json.loads(raw_keys)
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            keys.update({str(signer): str(key) for signer, key in parsed.items() if str(key).strip()})
    return keys


def verify_plugin_signature(manifest: dict[str, Any], signing_keys: dict[str, str] | None = None) -> dict[str, Any]:
    """Verify a plugin manifest signature against the signer's configured key."""

    signer = str(manifest.get("signer", "")).strip()
    signature = str(manifest.get(SIGNATURE_FIELD, "")).strip()
    signing_keys = signing_keys or load_plugin_signing_keys()

    if not signature:
        return {"valid": False, "status": "missing", "reason": "manifest signature is missing"}
    if not signer:
        return {"valid": False, "status": "invalid", "reason": "manifest signer is missing"}
    if signer not in signing_keys:
        return {"valid": False, "status": "unknown_signer", "reason": f"no signing key configured for signer '{signer}'"}

    expected = hmac.new(signing_keys[signer].encode("utf-8"), _canonical_manifest(manifest), hashlib.sha256).hexdigest()
    if hmac.compare_digest(signature, expected):
        return {"valid": True, "status": "valid", "reason": "signature verified"}
    return {"valid": False, "status": "invalid", "reason": "manifest signature does not match"}
