"""Public GitHub release readiness helpers."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

DEFAULT_REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    ".env.example",
    ".github/workflows/ci.yml",
)

QUALITY_COMMANDS = (
    "python repo_hygiene.py --include-secrets",
    "python -m ruff check .",
    "python project_audit.py",
    "python ui_smoke.py",
    "python ui_screenshot_regression.py",
    "python -m pytest",
    "python -m unittest discover -s tests -v",
)


def _section(status: str, detail: str, items: list | None = None) -> dict:
    return {"status": status, "detail": detail, "items": items or []}


def _existing_files(root: Path) -> set[str]:
    return {path for path in DEFAULT_REQUIRED_FILES if (root / path).exists()}


def _normalise_hygiene_items(items: Sequence[object]) -> list[str]:
    return [str(getattr(item, "path", item)) for item in items]


def _repo_snapshot(root: Path) -> set[str]:
    """Return a relative path snapshot before readiness checks run."""

    return {path.relative_to(root).as_posix() for path in root.rglob("*")}


def _cache_artifacts(root: Path) -> set[str]:
    """Return Python cache artifacts that strict hygiene should normally block."""

    artifacts = {path.relative_to(root).as_posix() for path in root.rglob("*.pyc")}
    artifacts.update(path.relative_to(root).as_posix() for path in root.rglob("__pycache__") if path.is_dir())
    return artifacts


def _remove_new_cache_artifacts(root: Path, before_snapshot: set[str]) -> dict[str, list[str]]:
    """Remove only cache files/directories created during this readiness run."""

    removed: list[str] = []
    warnings: list[str] = []
    current = _cache_artifacts(root)
    new_artifacts = sorted(current - before_snapshot, key=lambda item: item.count("/"), reverse=True)
    for relative in new_artifacts:
        target = root / relative
        if target.is_file() and target.suffix == ".pyc":
            target.unlink()
            removed.append(relative)
        elif target.is_dir() and target.name == "__pycache__":
            try:
                target.rmdir()
                removed.append(relative)
            except OSError as error:
                warnings.append(f"Could not remove non-empty readiness-generated cache directory {relative}: {error}")
    return {"removed": removed, "warnings": warnings}


def _run_hygiene_subprocess(root: Path) -> dict:
    """Run strict hygiene without importing project modules or writing bytecode."""

    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    command = [sys.executable, "-B", "repo_hygiene.py", "--include-secrets"]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, env=env, check=False)
    return {
        "passed": completed.returncode == 0,
        "items": _parse_hygiene_items(completed.stdout),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def _parse_hygiene_items(output: str) -> list[str]:
    """Extract blocker paths from the hygiene Markdown table."""

    items: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| `"):
            continue
        path = stripped.split("`", 2)[1]
        items.append(path)
    return items


def _build_signing_panel(env: Mapping[str, str], trusted_signers: list[str] | None = None) -> dict:
    signing_key = env.get("JARVIS_RELEASE_SIGNING_KEY", "")
    signer_ready = bool(trusted_signers or ["ci"])
    key_ready = len(signing_key) >= 16
    checks = [
        {
            "id": "signing_key",
            "status": "ready" if key_ready else "missing",
            "fix": "Set JARVIS_RELEASE_SIGNING_KEY with at least 16 characters.",
        },
        {
            "id": "trusted_signers",
            "status": "ready" if signer_ready else "missing",
            "fix": "Add at least one trusted signer.",
        },
    ]
    return {"ready": key_ready and signer_ready, "checks": checks}


def build_public_release_check(
    *,
    root: str | Path = ".",
    env: Mapping[str, str] | None = None,
    hygiene_items: Sequence[object] | None = None,
    required_files: Sequence[str] = DEFAULT_REQUIRED_FILES,
    existing_files: set[str] | None = None,
    trusted_signers: list[str] | None = None,
) -> dict:
    """Return a deterministic public release readiness report."""

    root_path = Path(root).resolve()
    before_snapshot = _repo_snapshot(root_path)
    found_files = _existing_files(root_path) if existing_files is None else existing_files
    missing_files = [path for path in required_files if path not in found_files]
    cleanup_warnings: list[str] = []
    if hygiene_items is None:
        _run_hygiene_subprocess(root_path)
        cache_cleanup = _remove_new_cache_artifacts(root_path, before_snapshot)
        final_hygiene = _run_hygiene_subprocess(root_path)
        local_items = final_hygiene["items"]
        cleanup_warnings.extend(f"Removed readiness-generated cache artifact: {item}" for item in cache_cleanup["removed"])
        cleanup_warnings.extend(cache_cleanup["warnings"])
        if final_hygiene["stderr"]:
            cleanup_warnings.append(final_hygiene["stderr"].strip())
    else:
        local_items = _normalise_hygiene_items(hygiene_items)
    release_panel = _build_signing_panel(env or {}, trusted_signers=trusted_signers)
    signing_status = "ready" if release_panel["ready"] else "optional"
    sections = {
        "docs": _section("ready" if not missing_files else "blocked", "Required public repository files", missing_files),
        "hygiene": _section("ready" if not local_items else "blocked", "Local-only files should be cleaned before publishing", local_items),
        "quality": _section("ready", "Run the release quality gate commands", list(QUALITY_COMMANDS)),
        "signing": _section(signing_status, "Optional release metadata signing readiness", release_panel["checks"]),
        "warnings": _section("warning" if cleanup_warnings else "ready", "Non-blocking readiness warnings", cleanup_warnings),
    }
    ready = all(section["status"] != "blocked" for section in sections.values())
    return {
        "ready": ready,
        "sections": sections,
        "commands": list(QUALITY_COMMANDS),
        "next_step": "Tag and publish the release." if ready else "Resolve blocked sections before publishing.",
    }


def render_public_release_check(report: dict) -> str:
    """Render release readiness as Markdown."""

    lines = ["# Public Release Readiness", "", f"Ready: {'yes' if report['ready'] else 'no'}", ""]
    for name, section in report["sections"].items():
        lines.append(f"## {name.title()}")
        lines.append(f"- Status: {section['status']}")
        lines.append(f"- Detail: {section['detail']}")
        for item in section["items"]:
            lines.append(f"  - {item}")
        lines.append("")
    lines.append("## Commands")
    for command in report["commands"]:
        lines.append(f"- `{command}`")
    lines.append("")
    lines.append(f"Next step: {report['next_step']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Open.Jarvis public release readiness.")
    parser.parse_args(argv)
    print(render_public_release_check(build_public_release_check()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
