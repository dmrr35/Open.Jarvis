"""Portable Windows package policy for Open.Jarvis release artifacts."""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

DEFAULT_APP_NAME = "Open.Jarvis"
DEFAULT_PLATFORM_SUFFIX = "windows-portable"
REQUIRED_ROOT_FILES = ("README_FIRST.txt", "LICENSE", ".env.example")
GUIDANCE_FOLDERS = ("plugins", "config", "optional_models", "docs")

DENIED_PARTS = {
    ".git",
    ".github",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "cache",
    "dist",
    "logs",
    "release",
    "temp",
    "tmp",
}
DENIED_SUFFIXES = {".pyc", ".log", ".jsonl", ".wav", ".mp3", ".m4a"}
GENERATED_IMAGE_SUFFIXES = {".screenshot", ".capture"}
SUSPICIOUS_FILENAME_RE = re.compile(r"(token|credential|credentials|secret|signing[-_]?key)", re.IGNORECASE)
WINDOWS_USER_PATH_RE = re.compile(r"C:\\Users\\", re.IGNORECASE)


def build_artifact_name(version: str, app_name: str = DEFAULT_APP_NAME) -> str:
    safe_version = str(version).strip().replace("/", "-").replace("\\", "-") or "dev"
    return f"{app_name}-{safe_version}-{DEFAULT_PLATFORM_SUFFIX}"


def expected_executable_path(app_name: str = DEFAULT_APP_NAME) -> str:
    return f"{app_name}/{app_name}.exe"


def normalize_portable_path(path: str | PurePosixPath) -> str:
    normalized = str(path).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_absolute_or_traversal_path(path: str) -> dict[str, object]:
    normalized = normalize_portable_path(path)
    posix = PurePosixPath(normalized)
    windows = PureWindowsPath(path)
    if normalized.startswith("/") or normalized.startswith("\\") or windows.is_absolute():
        return {"denied": True, "reason": "absolute path is not allowed"}
    if ".." in posix.parts:
        return {"denied": True, "reason": "ZIP traversal path is not allowed"}
    return {"denied": False, "reason": ""}


def is_denied_portable_path(path: str, *, app_name: str = DEFAULT_APP_NAME) -> dict[str, object]:
    normalized = normalize_portable_path(path)
    safety = is_absolute_or_traversal_path(path)
    if safety["denied"]:
        return safety
    posix = PurePosixPath(normalized)
    parts_lower = {part.lower() for part in posix.parts}
    name_lower = posix.name.lower()
    suffix = posix.suffix.lower()
    expected_exe = expected_executable_path(app_name).lower()

    if "logs" in parts_lower or suffix == ".log":
        return {"denied": True, "reason": "log files are not allowed"}
    if parts_lower & DENIED_PARTS:
        return {"denied": True, "reason": "generated or private directory is not allowed"}
    if name_lower == ".env" or (name_lower.endswith(".env") and name_lower != ".env.example"):
        return {"denied": True, "reason": ".env files are not allowed"}
    if name_lower == "memory.json" or name_lower.startswith("private_memory"):
        return {"denied": True, "reason": "private memory files are not allowed"}
    if suffix in DENIED_SUFFIXES:
        return {"denied": True, "reason": f"{suffix} files are not allowed"}
    if suffix in {".png", ".jpg", ".jpeg"} and any(marker in name_lower for marker in GENERATED_IMAGE_SUFFIXES):
        return {"denied": True, "reason": "generated screenshot artifacts are not allowed"}
    if suffix == ".zip":
        return {"denied": True, "reason": "unexpected nested archive is not allowed"}
    if suffix == ".exe" and normalized.lower() != expected_exe:
        return {"denied": True, "reason": "unexpected executable is not allowed"}
    if SUSPICIOUS_FILENAME_RE.search(normalized):
        return {"denied": True, "reason": "token, credential, secret, or signing-key filename is not allowed"}
    if WINDOWS_USER_PATH_RE.search(path):
        return {"denied": True, "reason": "local Windows user path is not allowed"}
    return {"denied": False, "reason": ""}


def portable_layout(version: str, app_name: str = DEFAULT_APP_NAME) -> dict[str, object]:
    artifact_name = build_artifact_name(version, app_name=app_name)
    return {
        "artifact_name": artifact_name,
        "expected_executable": expected_executable_path(app_name),
        "required_root_files": list(REQUIRED_ROOT_FILES),
        "guidance_folders": list(GUIDANCE_FOLDERS),
        "zip_name": f"{artifact_name}.zip",
    }
