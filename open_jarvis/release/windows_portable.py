"""Dry-run-capable Windows portable package workflow."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from open_jarvis.release.artifact_verifier import verify_release_artifact
from open_jarvis.release.portable_policy import DEFAULT_APP_NAME, GUIDANCE_FOLDERS, portable_layout

Runner = Callable[[Sequence[str]], int]


README_FIRST = """Open.Jarvis Windows Portable

Run Open.Jarvis/Open.Jarvis.exe to start the desktop assistant.

Copy .env.example to .env only if you want optional integrations such as Groq or Spotify.
Do not share .env, logs, memory files, tokens, credentials, screenshots, or generated audio in public issues.

This portable package is unsigned unless release notes explicitly say otherwise. Windows SmartScreen may show a warning.
Groq, Spotify, microphone, speaker/TTS, plugins, and offline models are optional.
Large Vosk/Piper/Ollama models are not bundled by default.
"""


def build_windows_portable_plan(
    version: str,
    *,
    output_dir: str | Path = "release",
    entrypoint: str = "arayuz.py",
    app_name: str = DEFAULT_APP_NAME,
) -> dict[str, object]:
    layout = portable_layout(version, app_name=app_name)
    artifact_name = str(layout["artifact_name"])
    output_path = Path(output_dir)
    pyinstaller_command = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        app_name,
        entrypoint,
    ]
    return {
        "version": version,
        "app_name": app_name,
        "entrypoint": entrypoint,
        "artifact_name": artifact_name,
        "portable_dir": str(output_path / artifact_name),
        "zip_path": str(output_path / f"{artifact_name}.zip"),
        "built_app_dir": str(Path("dist") / app_name),
        "pyinstaller_command": pyinstaller_command,
        "expected_executable": layout["expected_executable"],
        "required_root_files": layout["required_root_files"],
        "guidance_folders": layout["guidance_folders"],
    }


def _copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def assemble_portable_package(
    *,
    repo_root: str | Path,
    built_app_dir: str | Path,
    portable_dir: str | Path,
    app_name: str = DEFAULT_APP_NAME,
) -> dict[str, object]:
    repo = Path(repo_root)
    built = Path(built_app_dir)
    output = Path(portable_dir)
    if not built.exists():
        raise FileNotFoundError(f"Built app directory not found: {built}")
    exe = built / f"{app_name}.exe"
    if not exe.exists():
        raise FileNotFoundError(f"Expected executable not found: {exe}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    _copy_tree(built, output / app_name)
    for required in ("LICENSE", ".env.example"):
        source = repo / required
        if not source.exists():
            raise FileNotFoundError(f"Required package file missing: {source}")
        shutil.copy2(source, output / required)
    (output / "README_FIRST.txt").write_text(README_FIRST, encoding="utf-8")
    docs_output = output / "docs"
    docs_output.mkdir()
    docs_source = repo / "docs"
    for doc_name in ("WINDOWS_PORTABLE.md", "BUILD_WINDOWS.md", "VOICE_SETUP.md", "VOICE_TROUBLESHOOTING.md", "OFFLINE_STT.md", "PLUGIN_DEVELOPMENT.md", "PLUGIN_SECURITY.md", "RELEASE_SIGNING.md"):
        source = docs_source / doc_name
        if source.exists():
            shutil.copy2(source, docs_output / doc_name)
    for folder in GUIDANCE_FOLDERS:
        target = output / folder
        target.mkdir(exist_ok=True)
        readme = target / "README.txt"
        if not readme.exists():
            readme.write_text(f"{folder} is optional. Do not store secrets or private runtime data here before sharing packages.\n", encoding="utf-8")
    verification = verify_release_artifact(output, app_name=app_name)
    return {"status": "assembled" if verification["passed"] else "failed", "portable_dir": str(output), "verification": verification}


def _default_runner(command: Sequence[str]) -> int:
    return subprocess.run(list(command), check=False).returncode


def run_windows_portable_build(
    *,
    version: str,
    output_dir: str | Path = "release",
    entrypoint: str = "arayuz.py",
    app_name: str = DEFAULT_APP_NAME,
    dry_run: bool = False,
    clean: bool = False,
    skip_pyinstaller: bool = False,
    runner: Runner | None = None,
) -> dict[str, object]:
    plan = build_windows_portable_plan(version, output_dir=output_dir, entrypoint=entrypoint, app_name=app_name)
    output_path = Path(output_dir)
    if dry_run:
        return {"status": "dry_run", "plan": plan}
    if clean and output_path.exists():
        shutil.rmtree(output_path)
    if not skip_pyinstaller:
        exit_code = (runner or _default_runner)(plan["pyinstaller_command"])
        if exit_code != 0:
            return {"status": "failed", "reason": "pyinstaller failed", "exit_code": exit_code, "plan": plan}
    assembly = assemble_portable_package(repo_root=".", built_app_dir=plan["built_app_dir"], portable_dir=plan["portable_dir"], app_name=app_name)
    return {"status": assembly["status"], "plan": plan, "assembly": assembly}


def render_plan(result: dict[str, object]) -> str:
    plan = result.get("plan", result)
    lines = [
        f"Windows portable build status: {result.get('status', 'planned')}",
        f"Artifact: {plan['artifact_name']}",
        f"Portable directory: {plan['portable_dir']}",
        f"ZIP path: {plan['zip_path']}",
        "PyInstaller command:",
        "  " + " ".join(plan["pyinstaller_command"]),
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or dry-run an Open.Jarvis Windows portable package.")
    parser.add_argument("--version", default="dev", help="Portable artifact version label, for example v0.5.0.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands and paths without creating final artifacts.")
    parser.add_argument("--clean", action="store_true", help="Remove generated output directory before a real build.")
    parser.add_argument("--skip-pyinstaller", action="store_true", help="Assemble from an existing dist folder instead of running PyInstaller.")
    parser.add_argument("--output-dir", default="release", help="Generated output directory.")
    parser.add_argument("--entrypoint", default="arayuz.py", help="PyInstaller entrypoint.")
    parser.add_argument("--app-name", default=DEFAULT_APP_NAME, help="Executable/application folder name.")
    args = parser.parse_args(argv)
    result = run_windows_portable_build(
        version=args.version,
        output_dir=args.output_dir,
        entrypoint=args.entrypoint,
        app_name=args.app_name,
        dry_run=args.dry_run,
        clean=args.clean,
        skip_pyinstaller=args.skip_pyinstaller,
    )
    print(render_plan(result), end="")
    return 0 if result["status"] in {"dry_run", "assembled"} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
