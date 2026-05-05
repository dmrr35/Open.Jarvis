"""Windows release build planning for signed JARVIS artifacts."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from open_jarvis.security.release_security import build_release_manifest, sign_release_payload, verify_release_signature


def compute_file_sha256(path: str | Path) -> str:
    """Return the SHA256 digest for a release artifact."""

    import hashlib

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_release_artifacts(
    version: str,
    artifact_path: str | Path,
    output_dir: str | Path = "release",
    signer: str = "ci",
    signing_key: str | None = None,
) -> dict[str, Any]:
    """Compute, sign, verify, and write release metadata for a built artifact."""

    artifact_file = Path(artifact_path)
    if not artifact_file.exists():
        raise FileNotFoundError(f"Release artifact not found: {artifact_file}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    artifact = {
        "path": str(artifact_file),
        "name": artifact_file.name,
        "sha256": compute_file_sha256(artifact_file),
        "size_bytes": artifact_file.stat().st_size,
    }
    manifest = build_release_manifest(version, artifact, signer=signer)
    payload = {"version": version, "artifact": artifact}

    env_var = "JARVIS_RELEASE_SIGNING_KEY"
    previous_key = os.environ.get(env_var)
    if signing_key is not None:
        os.environ[env_var] = signing_key
    try:
        signature = sign_release_payload(payload, signer=signer)
        verification = verify_release_signature(payload, signature, signer=signer)
    finally:
        if signing_key is not None:
            if previous_key is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = previous_key

    safe_version = version.replace("/", "-").replace("\\", "-")
    manifest_path = output_path / f"jarvis-{safe_version}.manifest.json"
    signature_path = output_path / f"jarvis-{safe_version}.sig"
    metadata_path = output_path / f"jarvis-{safe_version}.release.json"
    metadata = {
        "version": version,
        "artifact": artifact,
        "manifest_path": str(manifest_path),
        "signature_path": str(signature_path),
        "metadata_path": str(metadata_path),
        "verification": verification,
    }

    _write_json(manifest_path, manifest)
    signature_path.write_text(signature + "\n", encoding="utf-8")
    _write_json(metadata_path, metadata)
    return metadata


def build_windows_release_plan(version: str, entrypoint: str = "arayuz.py", signing_ready: bool = False) -> dict:
    """Create a deterministic PyInstaller release plan without executing the build."""

    artifact_path = "dist/JARVIS.exe"
    artifact = {
        "path": artifact_path,
        "sha256": "computed-after-build",
        "entrypoint": entrypoint,
    }
    commands = [
        [
            "pyinstaller",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--name",
            "JARVIS",
            entrypoint,
        ],
        ["python", "-m", "compileall", "."],
        ["python", "-m", "unittest", "discover", "-s", "tests", "-q"],
    ]
    return {
        "status": "ready" if signing_ready else "blocked",
        "platform": "windows",
        "entrypoint": str(Path(entrypoint)),
        "artifact": artifact,
        "manifest": build_release_manifest(version, artifact, signer="ci"),
        "commands": commands,
        "signing_required": True,
        "next_step": "Run the commands, compute artifact sha256, sign the manifest, and publish both files.",
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for CI release artifact metadata generation."""

    import argparse

    parser = argparse.ArgumentParser(description="Build signed JARVIS release metadata for an existing artifact.")
    parser.add_argument("--version", required=True, help="Release version to record in the manifest.")
    parser.add_argument("--artifact", required=True, help="Path to the built JARVIS artifact.")
    parser.add_argument("--output-dir", default="release", help="Directory for manifest, signature, and metadata files.")
    parser.add_argument("--signer", default="ci", help="Release signer id. Defaults to ci.")
    parser.add_argument("--signing-key", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    result = build_release_artifacts(
        version=args.version,
        artifact_path=args.artifact,
        output_dir=args.output_dir,
        signer=args.signer,
        signing_key=args.signing_key,
    )
    print(f"Release manifest: {result['manifest_path']}")
    print(f"Release signature: {result['signature_path']}")
    print(f"Release verification: {result['verification']['reason']}")
    return 0 if result["verification"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
