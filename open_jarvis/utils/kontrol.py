"""JARVIS installation and health checker."""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from collections.abc import Mapping

from open_jarvis.health.observability import build_slo_report
from open_jarvis.integrations.provider_health import build_provider_health_checks
from open_jarvis.memory import build_memory_health_report, load_memory
from open_jarvis.release.project_audit import analyze_project, read_project_files
from open_jarvis.security.jarvis_admin import build_health_checks, render_health_report
from open_jarvis.security.release_security import load_release_policy


def _read_local_env(path: str = ".env") -> dict[str, str]:
    """Read local .env values for health checks without overriding process env."""

    values: dict[str, str] = {}
    if not os.path.exists(path):
        return values
    with open(path, encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def should_pause(argv: list[str] | None = None, env: Mapping[str, str] | None = None) -> bool:
    """Return whether the health command should wait for interactive input."""

    argv = sys.argv if argv is None else argv
    env = os.environ if env is None else env
    if "--no-pause" in argv:
        return False
    return env.get("CI", "").strip().lower() not in {"1", "true", "yes"}


def _check_internet() -> dict:
    try:
        urllib.request.urlopen("https://google.com", timeout=3)
        return {
            "id": "internet",
            "severity": "ok",
            "title": "Internet connection",
            "detail": "Network access is available.",
            "fix": "No action needed.",
        }
    except (OSError, urllib.error.URLError):
        return {
            "id": "internet",
            "severity": "warning",
            "title": "Internet connection",
            "detail": "Voice recognition and TTS may fail without internet.",
            "fix": "Connect to the internet, then rerun the health check.",
            "fix_command": "python kontrol.py --no-pause",
        }


def _check_chrome() -> dict:
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            return {
                "id": "chrome",
                "severity": "ok",
                "title": "Chrome installation",
                "detail": f"Chrome found at {path}.",
                "fix": "No action needed.",
            }
    return {
        "id": "chrome",
        "severity": "info",
        "title": "Chrome installation",
        "detail": "Chrome was not found in the standard locations.",
        "fix": "Install Chrome or add its path in the application launcher list.",
        "fix_command": "python kontrol.py --no-pause",
    }


def _check_python_version() -> dict:
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        severity = "ok"
        detail = f"Python {sys.version.split()[0]}."
        fix = "No action needed."
    else:
        severity = "warning"
        detail = f"Python {sys.version.split()[0]} is older than the recommended version."
        fix = "Upgrade to Python 3.11+ for the smoothest experience."
    return {
        "id": "python",
        "severity": severity,
        "title": "Python version",
        "detail": detail,
        "fix": fix,
    }


def _check_memory_health() -> dict:
    report = build_memory_health_report(load_memory())
    severity = "ok" if report["score"] >= 80 else "warning" if report["score"] >= 50 else "info"
    return {
        "id": "memory",
        "severity": severity,
        "title": "Memory health",
        "detail": f"Memory score: {report['score']}/100",
        "fix": report["recommendation"],
        "fix_command": 'python -c "from memory_store import prune_memory; prune_memory()"',
    }


def _check_runtime_posture() -> dict:
    report = build_slo_report()
    severity = "ok" if report["status"] == "healthy" else "warning" if report["status"] == "watch" else "critical"
    return {
        "id": "runtime",
        "severity": severity,
        "title": "Runtime posture",
        "detail": f"{report['events_seen']} recent events, {report['warning_count']} warnings, {report['error_count']} errors.",
        "fix": report["recommendation"],
        "fix_command": "python kontrol.py --no-pause",
    }


def _check_release_signing(env: Mapping[str, str] | None = None) -> dict:
    policy = load_release_policy()
    env = os.environ if env is None else env
    key_present = bool(env.get(policy["key_policy"]["env_var"], "").strip())
    return {
        "id": "release_signing",
        "severity": "ok" if key_present else "warning",
        "title": "Release signing",
        "detail": f"Trusted signers: {', '.join(policy.get('trusted_signers', []))}.",
        "fix": f"Set {policy['key_policy']['env_var']} with a rotated signing key before release builds.",
        "fix_command": "notepad .env",
    }


def _check_project_audit() -> dict:
    report = analyze_project(read_project_files("."))
    finding_count = len(report["findings"])
    return {
        "id": "project_audit",
        "severity": "ok" if finding_count == 0 else "warning",
        "title": "Project audit",
        "detail": f"{finding_count} finding(s) detected by static audit.",
        "fix": "Run python project_audit.py and address the recommendations one by one.",
        "fix_command": "python project_audit.py",
    }


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    print("=" * 72)
    print("   J.A.R.V.I.S  -  Installation & Health Check")
    print("=" * 72)

    local_env = {**_read_local_env(), **dict(os.environ)}

    checks = [
        _check_python_version(),
        _check_chrome(),
        _check_internet(),
        _check_memory_health(),
        _check_runtime_posture(),
        _check_release_signing(local_env),
        _check_project_audit(),
    ]
    checks.extend(build_health_checks(env=local_env))
    checks.extend(build_provider_health_checks(local_env, probe_local="--probe-providers" in argv))

    severity_order = {"critical": 0, "warning": 1, "info": 2, "ok": 3}
    checks = sorted(checks, key=lambda item: severity_order.get(item["severity"], 2))

    print()
    print(render_health_report(checks))

    criticals = [item for item in checks if item["severity"] == "critical"]
    warnings = [item for item in checks if item["severity"] == "warning"]

    print()
    print("=" * 72)
    if criticals:
        print("Critical issues found. Suggested recovery steps:")
        for item in criticals:
            print(f"- {item['fix']}")
    elif warnings:
        print("No critical blockers found, but there are warnings to review.")
        for item in warnings:
            print(f"- {item['fix']}")
    else:
        print("Everything looks ready. You can run:")
        print("  python arayuz.py")
        print("  python jarvis.py")

    print("=" * 72)
    if should_pause(argv):
        input("\nPress Enter to continue...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
