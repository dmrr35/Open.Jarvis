"""Public source-release safety scanner for Open J.A.R.V.I.S."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "cache",
    "dist",
    "env",
    "exports",
    "logs",
    "release",
    "temp",
    "tmp",
    "venv",
}

SKIP_SUFFIXES = {
    ".bmp",
    ".dll",
    ".exe",
    ".gif",
    ".ico",
    ".jpg",
    ".jpeg",
    ".m4a",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".pyd",
    ".pyc",
    ".sqlite",
    ".wav",
    ".webp",
}

BLOCKED_FILE_RE = re.compile(
    r"(^|[\\/])("
    r"\.env$|.*\.env$|.*token.*|.*credential.*|.*credentials.*|.*secret.*|"
    r"memory\.json$|config[\\/]settings\.json$|.*\.log$|.*\.jsonl$|.*\.sqlite$|.*\.db$"
    r")",
    re.IGNORECASE,
)

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
ENV_ASSIGN_RE = re.compile(
    r"^\s*([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|CLIENT_ID|REDIRECT_URI)[A-Z0-9_]*)=(.+?)\s*$",
)
GROQ_KEY_RE = re.compile(r"\bgsk_[A-Za-z0-9_-]{20,}\b")
OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
WINDOWS_USER_PATH_RE = re.compile(r"\bC:\\Users\\[^\\\s]+", re.IGNORECASE)
AUTH_HEADER_RE = re.compile(r"\b(authorization|bearer)\b\s*[:=]\s*['\"]?[^'\"\s]+", re.IGNORECASE)

SUSPICIOUS_WORDS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "password",
    "bearer",
    "authorization",
)

SAFE_PLACEHOLDER_VALUES = {
    "",
    "your_groq_api_key_here",
    "your_spotify_client_id_here",
    "your_spotify_client_secret_here",
    "your_redirect_uri_here",
    "your_gemini_api_key_here",
    "here_is_your_groq_api_key",
    "here_is_your_gemini_api_key",
    "here_is_your_spotify_client_id",
    "here_is_your_spotify_client_secret",
    "example@example.com",
    "http://127.0.0.1:8888/callback",
    "false",
    "true",
}

SAFE_EMAILS = {"example@example.com", "test@example.com"}
ALLOWED_PATTERN_FILES = {
    "privacy_mode.py",
    "public_release_check.py",
    "repo_hygiene.py",
    "test_public_release_check.py",
    "tests/test_public_release_check.py",
}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    reason: str
    excerpt: str

    def format(self) -> str:
        location = self.path.as_posix()
        line_part = f":{self.line}" if self.line else ""
        return f"- {location}{line_part} [{self.reason}] {self.excerpt}"


def _relative(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def _git_tracked_files(root: Path) -> list[Path] | None:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    files = [root / line.strip() for line in result.stdout.splitlines() if line.strip()]
    return files or None


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_root, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        base = Path(current_root)
        for name in names:
            files.append(base / name)
    return files


def iter_public_files(root: Path = ROOT) -> list[Path]:
    """Return public candidate files when possible, otherwise a source-tree approximation."""

    files = _git_tracked_files(root) or _walk_files(root)
    public_files: list[Path] = []
    for path in files:
        if not path.exists():
            continue
        rel = _relative(path, root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        public_files.append(path)
    return sorted(public_files)


def _is_safe_placeholder(value: str) -> bool:
    cleaned = value.strip().strip("'\"").lower()
    if cleaned in SAFE_PLACEHOLDER_VALUES:
        return True
    return cleaned.startswith("your_") or cleaned.endswith("_here") or cleaned.startswith("example")


def _scan_line(path: Path, rel: Path, line_number: int, line: str) -> list[Finding]:
    findings: list[Finding] = []
    rel_name = rel.as_posix()
    basename = rel.name
    stripped = line.strip()
    lower = stripped.lower()

    if basename in ALLOWED_PATTERN_FILES:
        return findings

    if match := ENV_ASSIGN_RE.match(stripped):
        key, value = match.groups()
        if not _is_safe_placeholder(value):
            findings.append(Finding(rel, line_number, f"secret-like assignment: {key}", _redact(stripped)))

    for email in EMAIL_RE.findall(line):
        if email.lower() not in SAFE_EMAILS and "example." not in email.lower():
            findings.append(Finding(rel, line_number, "real email pattern", _redact(email)))

    if GROQ_KEY_RE.search(line):
        findings.append(Finding(rel, line_number, "Groq API key pattern", _redact(stripped)))
    if OPENAI_KEY_RE.search(line):
        findings.append(Finding(rel, line_number, "OpenAI-style API key pattern", _redact(stripped)))
    if WINDOWS_USER_PATH_RE.search(line) and "C:\\Path\\To\\Your\\File" not in line:
        findings.append(Finding(rel, line_number, "machine-specific Windows user path", _redact(stripped)))
    if AUTH_HEADER_RE.search(line):
        findings.append(Finding(rel, line_number, "authorization header/token pattern", _redact(stripped)))

    if _looks_like_secret_value_context(lower) and not _looks_documented_or_code_reference(rel_name, lower):
        findings.append(Finding(rel, line_number, "suspicious credential wording", _redact(stripped)))

    return findings


def _looks_like_secret_value_context(lower_line: str) -> bool:
    """Return True for credential words paired with a likely literal value."""

    if not any(word in lower_line for word in SUSPICIOUS_WORDS):
        return False
    if any(token in lower_line for token in ("secret", "token", "password")) and any(token in lower_line for token in ("=", ":")):
        return any(marker in lower_line for marker in ("gsk_", "sk-", "bearer ", "access_token=", "refresh_token="))
    return False


def _looks_documented_or_code_reference(rel_name: str, lower_line: str) -> bool:
    if rel_name.endswith((".md", ".py", ".yml", ".yaml", ".txt", ".example")):
        if any(token in lower_line for token in ("placeholder", "example", "missing", "mask", "pattern", "never commit", "secret_keys")):
            return True
        if any(token in lower_line for token in ("os.getenv", "getenv", "client_secret", "spotify_client_secret")):
            return True
    return False


def _redact(value: str) -> str:
    if len(value) <= 120:
        return value
    return value[:117] + "..."


def scan_file(path: Path, root: Path = ROOT) -> list[Finding]:
    rel = _relative(path, root)
    if BLOCKED_FILE_RE.search(rel.as_posix()) and rel.name != ".env.example":
        return [Finding(rel, 0, "private runtime/credential filename", rel.name)]

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    findings: list[Finding] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        findings.extend(_scan_line(path, rel, line_number, line))
    return findings


def run_check(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_public_files(root):
        findings.extend(scan_file(path, root))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan public source files for secrets and private release blockers.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root to scan.")
    args = parser.parse_args()

    findings = run_check(args.root.resolve())
    print("PUBLIC SOURCE RELEASE CHECK:", "FAIL" if findings else "PASS")
    if findings:
        print("\nFindings:")
        for finding in findings:
            print(finding.format())
        return 1
    print("\nNo obvious secrets, private paths, token files, logs, cache artifacts, or private memory files detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
