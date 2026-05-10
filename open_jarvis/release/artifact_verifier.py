"""Verify generated Windows portable release artifacts before publishing."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

from open_jarvis.release.portable_policy import (
    REQUIRED_ROOT_FILES,
    expected_executable_path,
    is_denied_portable_path,
    normalize_portable_path,
)

TEXT_SUFFIXES = {".txt", ".md", ".json", ".example", ".ini", ".cfg", ".toml", ".yaml", ".yml"}
SECRET_RE = re.compile(r"(gsk_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|authorization\s*[:=]|bearer\s+|api_key\s*=\s*\S+)", re.IGNORECASE)
LOCAL_PATH_RE = re.compile(r"C:\\Users\\", re.IGNORECASE)


@dataclass(frozen=True)
class ArtifactFinding:
    path: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "reason": self.reason}


def _scan_text(path: str, content: bytes) -> list[ArtifactFinding]:
    suffix = Path(path).suffix.lower()
    if suffix not in TEXT_SUFFIXES and Path(path).name not in REQUIRED_ROOT_FILES:
        return []
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return []
    findings: list[ArtifactFinding] = []
    if SECRET_RE.search(text):
        findings.append(ArtifactFinding(path, "suspicious secret-like text"))
    if LOCAL_PATH_RE.search(text):
        findings.append(ArtifactFinding(path, "local path leakage"))
    return findings


def _verify_names(names: list[str], *, app_name: str) -> list[ArtifactFinding]:
    findings: list[ArtifactFinding] = []
    normalized_names = {normalize_portable_path(name).rstrip("/") for name in names}
    required = set(REQUIRED_ROOT_FILES) | {expected_executable_path(app_name)}
    for required_path in sorted(required):
        if required_path not in normalized_names:
            findings.append(ArtifactFinding(required_path, "required portable file is missing"))
    for name in sorted(normalized_names):
        if not name:
            continue
        denied = is_denied_portable_path(name, app_name=app_name)
        if denied["denied"]:
            findings.append(ArtifactFinding(name, str(denied["reason"])))
    return findings


def _verify_folder(path: Path, *, app_name: str) -> dict[str, object]:
    names: list[str] = []
    findings: list[ArtifactFinding] = []
    for item in path.rglob("*"):
        relative = item.relative_to(path).as_posix()
        names.append(relative)
        if item.is_file():
            try:
                findings.extend(_scan_text(relative, item.read_bytes()))
            except OSError as error:
                findings.append(ArtifactFinding(relative, f"could not read file: {error}"))
    findings.extend(_verify_names(names, app_name=app_name))
    return _result(findings, checked_files=len(names))


def _verify_zip(path: Path, *, app_name: str) -> dict[str, object]:
    findings: list[ArtifactFinding] = []
    try:
        with zipfile.ZipFile(path) as package:
            names = package.namelist()
            findings.extend(_verify_names(names, app_name=app_name))
            for info in package.infolist():
                if info.is_dir():
                    continue
                try:
                    findings.extend(_scan_text(info.filename, package.read(info)))
                except (OSError, RuntimeError, zipfile.BadZipFile) as error:
                    findings.append(ArtifactFinding(info.filename, f"could not read zip member: {error}"))
    except (OSError, zipfile.BadZipFile) as error:
        findings.append(ArtifactFinding(str(path), f"invalid zip artifact: {error}"))
        names = []
    return _result(findings, checked_files=len(names))


def _result(findings: list[ArtifactFinding], *, checked_files: int) -> dict[str, object]:
    return {
        "passed": not findings,
        "checked_files": checked_files,
        "findings": [finding.as_dict() for finding in findings],
    }


def verify_release_artifact(path: str | Path, *, app_name: str = "Open.Jarvis") -> dict[str, object]:
    artifact = Path(path)
    if not artifact.exists():
        return _result([ArtifactFinding(str(artifact), "artifact path does not exist")], checked_files=0)
    if artifact.is_dir():
        return _verify_folder(artifact, app_name=app_name)
    if artifact.suffix.lower() == ".zip":
        return _verify_zip(artifact, app_name=app_name)
    return _result([ArtifactFinding(str(artifact), "artifact must be a portable folder or zip")], checked_files=0)


def render_verification(result: dict[str, object]) -> str:
    lines = [f"WINDOWS PORTABLE ARTIFACT: {'PASS' if result['passed'] else 'FAIL'}", f"Checked files: {result['checked_files']}"]
    findings = result.get("findings", [])
    if findings:
        lines.append("Findings:")
        for finding in findings:
            lines.append(f"- {finding['path']}: {finding['reason']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify an Open.Jarvis Windows portable folder or ZIP.")
    parser.add_argument("artifact", nargs="?", help="Portable folder or ZIP to verify.")
    parser.add_argument("--app-name", default="Open.Jarvis", help="Expected app/executable folder name.")
    args = parser.parse_args(argv)
    if not args.artifact:
        parser.print_help()
        return 0
    result = verify_release_artifact(args.artifact, app_name=args.app_name)
    print(render_verification(result), end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
