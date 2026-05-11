"""Check and clean local-only files before publishing JARVIS."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HygieneItem:
    """A generated or secret local path that should not be published."""

    path: str
    reason: str
    secret: bool = False


HYGIENE_ITEMS = (
    HygieneItem(".env", "local secret environment file", secret=True),
    HygieneItem(".coverage", "coverage database"),
    HygieneItem(".pytest_cache", "pytest cache directory"),
    HygieneItem(".mypy_cache", "mypy cache directory"),
    HygieneItem(".ruff_cache", "ruff cache directory"),
    HygieneItem("__pycache__", "python bytecode cache"),
    HygieneItem("build", "PyInstaller build directory"),
    HygieneItem("dist", "compiled release output"),
    HygieneItem("exports", "generated eval and screenshot artifacts"),
    HygieneItem("logs", "runtime log directory"),
    HygieneItem("memory.json", "local assistant memory data"),
    HygieneItem("config/settings.json", "local user settings file"),
    HygieneItem("release", "generated release metadata directory"),
)

SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", "build", "dist", "exports", "logs", "release"}
SKIP_SUFFIXES = {
    ".bmp",
    ".db",
    ".dll",
    ".exe",
    ".gif",
    ".ico",
    ".jpg",
    ".jpeg",
    ".mp3",
    ".mp4",
    ".pyd",
    ".pyc",
    ".png",
    ".sqlite",
    ".wav",
    ".webp",
    ".zip",
}
SECRET_PATTERN = re.compile(r"\b(GROQ_API_KEY|SPOTIFY_CLIENT_SECRET|api_key|secret|token)\s*=\s*([^\s#]+)", re.IGNORECASE)
PLACEHOLDER_VALUES = {
    "",
    "abc",
    "abc123",
    "example",
    "here_is_your_groq_api_key",
    "here_is_your_spotify_client_secret",
    "secret",
    "smoke",
    "test",
    "token",
    "true",
    "false",
    "***",
    "your_groq_api_key_here",
    "your_spotify_client_secret_here",
}


def _is_inside_root(root: Path, candidate: Path) -> bool:
    root = root.resolve()
    candidate = candidate.resolve()
    return candidate == root or root in candidate.parents


def _is_placeholder_secret(value: str) -> bool:
    raw = value.strip().strip(" ,)]}\"'")
    raw = raw.split("\\n", 1)[0]
    cleaned = raw.lower()
    return (
        cleaned in PLACEHOLDER_VALUES
        or cleaned.rstrip('",').endswith("=")
        or cleaned.startswith(("your_", "here_", "<", "${{"))
        or raw.isupper()
        or "(" in raw
        or ")" in raw
    )


def _iter_text_files(root_path: Path):
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = set(path.relative_to(root_path).parts[:-1])
        if relative_parts & SKIP_DIRS or "tests" in relative_parts:
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def find_secret_patterns(root: str | Path = ".") -> list[HygieneItem]:
    """Return suspicious non-placeholder secret assignments in text files."""

    root_path = Path(root)
    findings: list[HygieneItem] = []
    for path in _iter_text_files(root_path):
        relative = path.relative_to(root_path).as_posix()
        if relative == ".env.example":
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if "os.getenv" in line or "os.environ" in line:
                continue
            for match in SECRET_PATTERN.finditer(line):
                value = match.group(2)
                if _is_placeholder_secret(value):
                    continue
                findings.append(
                    HygieneItem(
                        f"{relative}:{line_number}",
                        f"possible secret assignment for {match.group(1)}",
                        secret=True,
                    )
                )
    return findings


def _remove_tree(target: Path) -> None:
    def handle_remove_error(function, path, _exc_info):
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(target, onerror=handle_remove_error)


def find_hygiene_items(root: str | Path = ".", *, include_secrets: bool = True) -> list[HygieneItem]:
    """Return local-only paths that currently exist under the project root."""

    root_path = Path(root)
    found = []
    for item in HYGIENE_ITEMS:
        if item.secret and not include_secrets:
            continue
        path = root_path / item.path
        if path.exists():
            found.append(item)
    for cache_dir in root_path.rglob("__pycache__"):
        relative = cache_dir.relative_to(root_path).as_posix()
        if relative != "__pycache__":
            found.append(HygieneItem(relative, "nested python bytecode cache"))
    for pyc_path in root_path.rglob("*.pyc"):
        found.append(HygieneItem(pyc_path.relative_to(root_path).as_posix(), "python bytecode file"))
    for artifact_pattern, reason in {
        "*.exe": "compiled executable artifact",
        "*.log": "runtime log file",
        "*.jsonl": "runtime event stream",
        "*.zip": "generated archive",
        "*.tar.gz": "generated archive",
        "*.spec": "PyInstaller spec artifact",
    }.items():
        for artifact_path in root_path.rglob(artifact_pattern):
            relative = artifact_path.relative_to(root_path).as_posix()
            if relative == ".env.example":
                continue
            found.append(HygieneItem(relative, reason))
    for exe_path in root_path.glob("*.exe"):
        found.append(HygieneItem(exe_path.name, "compiled executable artifact"))
    if include_secrets:
        found.extend(find_secret_patterns(root_path))
    return sorted({item.path: item for item in found}.values(), key=lambda item: item.path)


def clean_hygiene_items(root: str | Path = ".", *, include_secrets: bool = False) -> list[str]:
    """Delete generated local files. Secret deletion requires include_secrets=True."""

    root_path = Path(root).resolve()
    removed = []
    for item in find_hygiene_items(root_path, include_secrets=include_secrets):
        target = root_path / item.path
        if not _is_inside_root(root_path, target):
            continue
        if target.is_dir():
            _remove_tree(target)
        elif target.exists():
            target.unlink()
        else:
            continue
        removed.append(item.path)
    return removed


def render_hygiene_report(items: list[HygieneItem]) -> str:
    """Render a compact report for release preparation."""

    lines = ["# Repository Hygiene", "", f"PUBLIC RELEASE HYGIENE: {'FAIL' if items else 'PASS'}", ""]
    if not items:
        lines.append("- No local-only files detected.")
        return "\n".join(lines) + "\n"
    lines.append("| Path | Reason | Secret |")
    lines.append("| --- | --- | --- |")
    for item in items:
        lines.append(f"| `{item.path}` | {item.reason} | {'yes' if item.secret else 'no'} |")
    lines.extend(["", "Run `python repo_hygiene.py --clean` to remove generated files."])
    lines.append("Use `--include-secrets` only after backing up or rotating local API keys.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local-only files before publishing JARVIS.")
    parser.add_argument("--clean", action="store_true", help="remove generated local files")
    parser.add_argument("--include-secrets", action="store_true", help="also include .env in checks or cleanup")
    args = parser.parse_args()

    if args.clean:
        removed = clean_hygiene_items(".", include_secrets=args.include_secrets)
        print(render_hygiene_report([HygieneItem(path, "removed") for path in removed]))
        return 0

    items = find_hygiene_items(".", include_secrets=args.include_secrets)
    print(render_hygiene_report(items))
    return 1 if items else 0


if __name__ == "__main__":
    raise SystemExit(main())
