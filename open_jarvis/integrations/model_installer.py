"""Safe local model installer planning for offline JARVIS profiles."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any

_MODELS = {
    "vosk-small-en-us": {
        "id": "vosk-small-en-us",
        "type": "stt",
        "provider": "Vosk",
        "manual_download_url": "https://alphacephei.com/vosk/models",
        "env_var": "JARVIS_VOSK_MODEL_PATH",
        "sha256": "a74639497a8a390df903e58a2a513e0fea5db9ceb86e3f76ea2a2e9f49cfc2af",
    },
    "piper-en-us": {
        "id": "piper-en-us",
        "type": "tts",
        "provider": "Piper",
        "manual_download_url": "https://github.com/rhasspy/piper/releases",
        "env_var": "JARVIS_TTS_PROVIDER",
        "sha256": "9b1f8f8f4b8ff7d8de3d8e6f0a8a98d3b46b65d2b407b943cc48c4b87abf8e6d",
    },
    "ollama-local": {
        "id": "ollama-local",
        "type": "llm",
        "provider": "Ollama",
        "manual_download_url": "https://ollama.com/download",
        "env_var": "JARVIS_LOCAL_LLM_URL",
        "sha256": "5a4f0e4b67a2c7ad0dd98fc71e7f25e7775fd5226f7198b3a7d873ba4fbe1d91",
    },
}


def _catalog_payload(catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": catalog.get("schema_version", 1),
        "models": catalog.get("models", []),
        "signer": catalog.get("signer", "ci"),
        "signature_algorithm": catalog.get("signature_algorithm", "hmac-sha256"),
    }


def _sign_catalog_payload(payload: dict[str, Any], signing_key: str) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(signing_key.encode("utf-8"), serialized, hashlib.sha256).hexdigest()


def build_signed_model_catalog(signing_key: str, signer: str = "ci") -> dict[str, Any]:
    """Build a signed checksum catalog for supported offline model profiles."""

    models = []
    for model in sorted(_MODELS.values(), key=lambda item: item["id"]):
        item = dict(model)
        item["expected_sha256"] = item["sha256"]
        models.append(item)
    payload = {
        "schema_version": 1,
        "models": models,
        "signer": signer,
        "signature_algorithm": "hmac-sha256",
    }
    return {**payload, "signature": _sign_catalog_payload(payload, signing_key)}


def verify_model_catalog(
    catalog: dict[str, Any],
    signing_key: str,
    trusted_signers: list[str] | None = None,
) -> dict[str, Any]:
    """Verify a signed model catalog before using its checksums."""

    trusted_signers = trusted_signers or ["ci"]
    signer = str(catalog.get("signer", ""))
    if signer not in trusted_signers:
        return {"status": "invalid", "reason": "untrusted signer", "models": [], "trusted_signer": ""}
    if not signing_key or len(signing_key) < 16:
        return {"status": "invalid", "reason": "missing signing key", "models": [], "trusted_signer": ""}
    signature = str(catalog.get("signature", ""))
    expected = _sign_catalog_payload(_catalog_payload(catalog), signing_key)
    if not hmac.compare_digest(signature, expected):
        return {"status": "invalid", "reason": "signature mismatch", "models": [], "trusted_signer": signer}
    return {"status": "verified", "reason": "signature matched", "models": list(catalog.get("models", [])), "trusted_signer": signer}


def _model_from_catalog(model_id: str, catalog: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if not catalog:
        return dict(_MODELS.get(model_id, {})), {"status": "not_provided", "reason": "No signed catalog was provided."}
    models = {item.get("id"): dict(item) for item in catalog.get("models", [])}
    model = models.get(model_id, {})
    return model, {
        "status": "verified" if model else "missing",
        "reason": "Model checksum loaded from signed catalog." if model else "Model not found in signed catalog.",
    }


def build_model_install_plan(model_id: str, target_dir: str = "models", catalog: dict[str, Any] | None = None) -> dict:
    """Build a safe manual install plan for a supported local model."""

    model, catalog_verification = _model_from_catalog(model_id, catalog)
    if not model:
        model = dict(_MODELS.get(model_id, {}))
    if not model:
        return {"status": "unsupported", "model": {"id": model_id}, "steps": [], "catalog_verification": catalog_verification}
    target = Path(target_dir) / model_id
    steps = [
        {
            "id": "create_target",
            "title": "Create model directory",
            "command": f"mkdir {target}",
            "safe": True,
        },
        {
            "id": "download_model",
            "title": "Download model manually from the official provider",
            "command": f"open {model['manual_download_url']}",
            "safe": True,
        },
        {
            "id": "verify_checksum",
            "title": "Verify the downloaded archive checksum",
            "command": f"python -c \"from model_installer import verify_model_checksum; print(verify_model_checksum('model.zip', '{model.get('sha256', '')}'))\"",
            "safe": True,
        },
        {
            "id": "configure_env",
            "title": f"Set {model['env_var']}",
            "command": "notepad .env",
            "safe": True,
        },
    ]
    return {"status": "ready", "model": model, "target_dir": str(target), "steps": steps, "catalog_verification": catalog_verification}


def verify_model_checksum(file_path: Path | str, expected_sha256: str) -> dict:
    """Verify a downloaded model archive against an expected SHA256."""

    path = Path(file_path)
    if not path.exists():
        return {"status": "missing", "path": str(path), "expected_sha256": expected_sha256, "actual_sha256": ""}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    status = "verified" if digest.lower() == expected_sha256.lower() else "mismatch"
    return {
        "status": status,
        "path": str(path),
        "expected_sha256": expected_sha256,
        "actual_sha256": digest,
    }


def write_signed_model_catalog(output_path: Path | str, signing_key: str, signer: str = "ci") -> dict[str, Any]:
    """Write a signed model catalog JSON file."""

    catalog = build_signed_model_catalog(signing_key=signing_key, signer=signer)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verification = verify_model_catalog(catalog, signing_key=signing_key, trusted_signers=[signer])
    return {"path": str(path), "catalog": catalog, "verification": verification}


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for signed model catalog generation."""

    import argparse

    parser = argparse.ArgumentParser(description="Build and verify signed JARVIS offline model catalogs.")
    parser.add_argument("--write-catalog", help="Write a signed model catalog to this path.")
    parser.add_argument("--signer", default="ci", help="Catalog signer id.")
    parser.add_argument("--signing-key", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if not args.write_catalog:
        parser.print_help()
        return 0
    env_key = os.getenv("JARVIS_RELEASE_SIGNING_KEY", "")
    signing_key = args.signing_key or env_key
    if not signing_key or len(signing_key) < 16:
        print("Model catalog signing key is missing or too short.")
        return 1
    result = write_signed_model_catalog(args.write_catalog, signing_key=signing_key, signer=args.signer)
    print(f"Model catalog: {result['path']}")
    print(f"Model catalog verification: {result['verification']['reason']}")
    return 0 if result["verification"]["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
