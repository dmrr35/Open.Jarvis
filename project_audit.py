"""Static project audit helpers for maintainability and product readiness."""

from __future__ import annotations

from pathlib import Path

DEFAULT_PATTERNS = {
    "unsafe_process_calls": ["os.system(", "subprocess.run(", "subprocess.Popen("],
    "broad_exception_handlers": ["except Exception"],
    "silent_failures": ["pass\n"],
}
IGNORED_PARTS = {"__pycache__", ".ruff_cache", ".mypy_cache"}
AUDIT_ONLY_FILES = {"project_audit.py"}
CENTRAL_PROCESS_WRAPPERS = {"process_runner.py", "public_release.py", "scripts/public_release_check.py"}
REQUIRED_OSS_FILES = {
    "README.md": "Project overview and setup instructions",
    "LICENSE": "Explicit open-source usage terms",
    "CHANGELOG.md": "Release history and notable changes",
    "CONTRIBUTING.md": "Contribution workflow",
    "CODE_OF_CONDUCT.md": "Community behavior expectations",
    "SECURITY.md": "Vulnerability reporting policy",
    ".github/pull_request_template.md": "Pull request checklist",
    ".github/ISSUE_TEMPLATE/bug_report.md": "Bug report template",
    ".github/ISSUE_TEMPLATE/feature_request.md": "Feature request template",
    ".github/ISSUE_TEMPLATE/performance_report.md": "Performance issue template",
    ".github/ISSUE_TEMPLATE/plugin_review.md": "Plugin review template",
    ".github/workflows/ci.yml": "Continuous integration workflow",
}


RECOMMENDATIONS = {
    "large_files": "Split large modules by responsibility and keep compatibility wrappers during migration.",
    "unsafe_process_calls": "Route process/system calls through explicit safety gates and argument-list subprocess calls.",
    "broad_exception_handlers": "Replace broad exception handling with targeted exceptions plus actionable error messages.",
    "silent_failures": "Log or surface silent failures so health checks can diagnose them.",
    "low_test_surface": "Add focused tests around runtime safety, onboarding, release, and command dispatch edges.",
    "oss_readiness": "Add the missing public repository files before publishing on GitHub.",
}


def read_project_files(root: str | Path = ".") -> dict[str, str]:
    """Read text project files that are useful for static auditing."""

    root = Path(root)
    files = {}
    allowed_suffixes = {".py", ".md", ".json", ".yml", ".yaml"}
    allowed_names = {"LICENSE"}
    for path in root.rglob("*"):
        if path.is_file() and (path.suffix.lower() in allowed_suffixes or path.name in allowed_names):
            if any(part in IGNORED_PARTS for part in path.parts):
                continue
            try:
                files[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
    return files


def analyze_project(files: dict[str, str], large_file_threshold: int = 500) -> dict:
    """Return prioritized findings and recommendations for a project snapshot."""

    findings = []
    large_files = [
        {"path": path, "lines": content.count("\n") + 1}
        for path, content in files.items()
        if path.endswith(".py") and content.count("\n") + 1 > large_file_threshold
    ]
    if large_files:
        findings.append({"id": "large_files", "severity": "warning", "items": large_files})

    for finding_id, patterns in DEFAULT_PATTERNS.items():
        matches = []
        for path, content in files.items():
            normalized_path = path.replace("\\", "/")
            if normalized_path.startswith("tests/"):
                continue
            if normalized_path in AUDIT_ONLY_FILES:
                continue
            if finding_id == "unsafe_process_calls" and normalized_path in CENTRAL_PROCESS_WRAPPERS:
                continue
            for pattern in patterns:
                count = content.count(pattern)
                if count:
                    matches.append({"path": path, "pattern": pattern.strip(), "count": count})
        if matches:
            findings.append({"id": finding_id, "severity": "warning", "items": matches})

    normalized_paths = [path.replace("\\", "/") for path in files]
    test_count = len([path for path in normalized_paths if path.startswith("tests/") and path.endswith(".py")])
    source_count = len([path for path in normalized_paths if path.endswith(".py") and not path.startswith("tests/")])
    test_case_count = sum(
        content.count("def test_")
        for path, content in files.items()
        if path.replace("\\", "/").startswith("tests/") and path.endswith(".py")
    )
    if source_count and test_count / source_count < 0.35 and test_case_count / source_count < 1.0:
        findings.append(
            {
                "id": "low_test_surface",
                "severity": "info",
                "items": [{"source_files": source_count, "test_files": test_count, "test_cases": test_case_count}],
            }
        )

    missing_oss_files = [
        {"path": path, "purpose": purpose}
        for path, purpose in REQUIRED_OSS_FILES.items()
        if path not in normalized_paths
    ]
    if missing_oss_files:
        findings.append({"id": "oss_readiness", "severity": "warning", "items": missing_oss_files})

    recommendations = [
        {"id": finding["id"], "text": RECOMMENDATIONS[finding["id"]]} for finding in findings if finding["id"] in RECOMMENDATIONS
    ]
    return {"findings": findings, "recommendations": recommendations}


def render_markdown_report(report: dict) -> str:
    """Render a compact Markdown audit report."""

    lines = ["# JARVIS Project Audit", "", "## Findings"]
    if not report["findings"]:
        lines.append("- No static findings detected.")
    for finding in report["findings"]:
        lines.append(f"- {finding['severity'].upper()} `{finding['id']}`: {len(finding['items'])} item(s)")

    lines.extend(["", "## Recommendations"])
    if not report["recommendations"]:
        lines.append("- Keep current quality gates running.")
    for recommendation in report["recommendations"]:
        lines.append(f"- `{recommendation['id']}`: {recommendation['text']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = analyze_project(read_project_files("."))
    print(render_markdown_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
