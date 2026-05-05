"""Isolated plugin execution planning for trusted JARVIS plugins."""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from shutil import copytree, rmtree
from subprocess import DEVNULL, TimeoutExpired, run
from typing import Any

from plugin_security import build_plugin_sandbox_policy, validate_plugin_manifest
from plugin_signature import verify_plugin_signature


def _resolve_entrypoint(plugin_dir: Path, entrypoint: str) -> Path | None:
    root = plugin_dir.resolve()
    candidate = (root / entrypoint).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def build_resource_limits(sandbox: dict | None = None) -> dict[str, Any]:
    """Return explicit plugin resource limits for subprocess execution."""

    sandbox = sandbox or build_plugin_sandbox_policy()
    memory_mb = int(sandbox.get("max_memory_mb", 256))
    return {
        "timeout_seconds": float(sandbox.get("timeout_seconds", 30)),
        "max_memory_mb": memory_mb,
        "process_spawn": bool(sandbox.get("process_spawn", False)),
        "network": sandbox.get("network", "restricted"),
        "filesystem": sandbox.get("filesystem", "scoped"),
        "job_object": {
            "enabled": sys.platform == "win32",
            "memory_limit_bytes": memory_mb * 1024 * 1024,
            "kill_on_close": True,
        },
    }


def _copy_plugin_to_workspace(plugin_dir: Path, plugin_name: str) -> Path:
    safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in plugin_name) or "plugin"
    workspace_root = Path(tempfile.mkdtemp(prefix=f"jarvis_plugin_{safe_name}_"))
    workspace_plugin = workspace_root / "plugin"
    copytree(plugin_dir, workspace_plugin, dirs_exist_ok=False)
    return workspace_plugin


def build_plugin_execution_plan(
    plugin_dir: Path | str,
    manifest: dict,
    trusted_signers: list[str] | None = None,
    signing_keys: dict[str, str] | None = None,
) -> dict:
    """Build a subprocess execution plan after manifest and path validation."""

    plugin_dir = Path(plugin_dir)
    validation = validate_plugin_manifest(manifest, trusted_signers=trusted_signers)
    signature = verify_plugin_signature(manifest, signing_keys=signing_keys)
    sandbox = build_plugin_sandbox_policy()
    limits = build_resource_limits(sandbox)
    entrypoint = str(manifest.get("entrypoint", "")).strip()
    resolved = _resolve_entrypoint(plugin_dir, entrypoint) if entrypoint else None
    issues = list(validation["issues"])
    if not signature["valid"]:
        issues.append(signature["reason"])
    if resolved is None:
        issues.append("entrypoint resolves outside the plugin directory")
    elif not resolved.exists():
        issues.append("entrypoint file does not exist")

    if issues:
        return {
            "status": "blocked",
            "issues": issues,
            "signature_status": signature["status"],
            "sandbox": sandbox,
            "manifest": dict(manifest),
        }

    return {
        "status": "ready",
        "issues": [],
        "signature_status": signature["status"],
        "sandbox": sandbox,
        "manifest": dict(manifest),
        "execution": {
            "mode": "subprocess",
            "command": [sys.executable, str(resolved)],
            "cwd": str(plugin_dir.resolve()),
            "timeout_seconds": limits["timeout_seconds"],
            "resource_limits": limits,
            "env": {"PYTHONNOUSERSITE": "1"},
        },
    }


def run_plugin_in_sandbox(
    plugin_dir: Path | str,
    manifest: dict,
    trusted_signers: list[str] | None = None,
    signing_keys: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Execute a trusted plugin inside a temporary scoped workspace."""

    plan = build_plugin_execution_plan(plugin_dir, manifest, trusted_signers=trusted_signers, signing_keys=signing_keys)
    if plan["status"] != "ready":
        return {"status": "blocked", "issues": plan["issues"], "plan": plan}

    plugin_name = str(manifest.get("name", "plugin"))
    workspace_plugin = _copy_plugin_to_workspace(Path(plugin_dir).resolve(), plugin_name)
    workspace_root = workspace_plugin.parent
    entrypoint = str(manifest.get("entrypoint", "")).strip()
    workspace_entrypoint = _resolve_entrypoint(workspace_plugin, entrypoint)
    limits = dict(plan["execution"]["resource_limits"])
    effective_timeout = float(timeout_seconds if timeout_seconds is not None else limits["timeout_seconds"])
    limits["timeout_seconds"] = effective_timeout
    start = time.perf_counter()
    result: dict[str, Any]
    deleted = False

    try:
        completed = run(
            [sys.executable, str(workspace_entrypoint)],
            cwd=str(workspace_plugin),
            env={"PYTHONNOUSERSITE": "1"},
            stdin=DEVNULL,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
            check=False,
        )
        result = {
            "status": "completed" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "error": "",
        }
    except TimeoutExpired as exc:
        result = {
            "status": "timeout",
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "error": f"Plugin execution timed out after {effective_timeout} seconds.",
        }
    finally:
        try:
            rmtree(workspace_root)
            deleted = True
        except OSError:
            deleted = False

    result.update(
        {
            "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            "workspace": {"path": str(workspace_root), "deleted": deleted},
            "resource_limits": limits,
            "plan": plan,
        }
    )
    return result
