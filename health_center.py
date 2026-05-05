"""Health center aggregation for UI and console diagnostics."""

from __future__ import annotations

import datetime as _dt
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jarvis_logging import LOG_FILE
from memory_store import prune_memory
from observability import EVENT_LOG, record_runtime_event

SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2, "ok": 3}
DEFAULT_FIX_COMMANDS = {
    "critical": "python kontrol.py --no-pause",
    "warning": "python kontrol.py --no-pause",
    "info": "python kontrol.py --no-pause",
    "ok": "",
}
SAFE_FIXES = {
    "memory": {
        "fix_id": "prune_memory",
        "title": "Prune memory",
        "detail": "Trim old notes and low-value memory growth while keeping recent data.",
    },
    "runtime": {
        "fix_id": "rotate_logs",
        "title": "Rotate runtime logs",
        "detail": "Archive current runtime logs so the next health check starts from a clean event window.",
    },
}


def build_fix_plan(check: dict) -> dict[str, Any]:
    """Return a safe, UI-friendly remediation plan for one health check."""

    fix = SAFE_FIXES.get(str(check.get("id", "")))
    if fix and check.get("severity") != "ok":
        return {
            **fix,
            "available": True,
            "mode": "safe",
            "dry_run": f"Would run: {fix['title']}. {fix['detail']}",
        }
    return {
        "fix_id": None,
        "title": "Manual review required",
        "available": False,
        "mode": "manual",
        "dry_run": "No one-click repair is available for this check.",
    }


def build_health_center(checks: list[dict]) -> dict:
    """Prioritize checks and attach executable fix hints."""

    enriched = []
    for check in checks:
        severity = check.get("severity", "info")
        enriched.append(
            {
                **check,
                "priority": SEVERITY_RANK.get(severity, 2),
                "fix_command": check.get("fix_command", DEFAULT_FIX_COMMANDS.get(severity, "")),
                "fix_plan": build_fix_plan(check),
            }
        )
    enriched.sort(key=lambda item: (item["priority"], item.get("id", "")))
    return {
        "checks": enriched,
        "summary": {
            "critical": sum(1 for item in enriched if item.get("severity") == "critical"),
            "warning": sum(1 for item in enriched if item.get("severity") == "warning"),
            "info": sum(1 for item in enriched if item.get("severity") == "info"),
            "ok": sum(1 for item in enriched if item.get("severity") == "ok"),
            "safe_fixes": sum(1 for item in enriched if item.get("fix_plan", {}).get("available")),
        },
    }


def _default_fix_handlers() -> dict[str, Callable[[], Any]]:
    return {"prune_memory": prune_memory, "rotate_logs": rotate_logs}


def rotate_logs(log_files: list[Path] | None = None, *, timestamp: str | None = None) -> dict[str, Any]:
    """Archive current local log files without deleting their contents."""

    stamp = timestamp or _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    files = log_files or [EVENT_LOG, LOG_FILE]
    rotated = []
    skipped = []
    for log_file in files:
        path = Path(log_file)
        if not path.exists() or path.stat().st_size == 0:
            skipped.append({"path": str(path), "reason": "missing_or_empty"})
            continue
        archive = path.with_name(f"{path.name}.{stamp}.bak")
        path.replace(archive)
        rotated.append({"path": str(path), "archive": str(archive)})
    status = "rotated" if rotated else "skipped"
    return {"status": status, "rotated": rotated, "skipped": skipped}


EventRecorder = Callable[[str, str, str, dict[str, Any] | None], None]


def _record_health_fix_event(
    event_recorder: EventRecorder,
    *,
    event_type: str,
    fix_id: str,
    status: str,
    dry_run: bool,
    severity: str = "info",
) -> None:
    event_recorder(
        event_type,
        f"Health fix {fix_id} {status}.",
        severity,
        {"fix_id": fix_id, "status": status, "dry_run": dry_run},
    )


def apply_health_fix(
    fix_id: str,
    *,
    dry_run: bool = True,
    handlers: dict[str, Callable[[], Any]] | None = None,
    event_recorder: EventRecorder = record_runtime_event,
) -> dict[str, Any]:
    """Apply a known safe health fix, or describe what would happen."""

    handlers = _default_fix_handlers() if handlers is None else handlers
    if fix_id not in handlers:
        _record_health_fix_event(
            event_recorder,
            event_type="health_fix_unsupported",
            fix_id=fix_id,
            status="unsupported",
            dry_run=dry_run,
            severity="warning",
        )
        return {"fix_id": fix_id, "status": "unsupported", "detail": "This health fix is not registered as a safe one-click repair."}
    if dry_run:
        _record_health_fix_event(event_recorder, event_type="health_fix_dry_run", fix_id=fix_id, status="dry_run", dry_run=True)
        return {"fix_id": fix_id, "status": "dry_run", "detail": f"Would apply safe fix: {fix_id}."}
    handlers[fix_id]()
    _record_health_fix_event(event_recorder, event_type="health_fix_applied", fix_id=fix_id, status="applied", dry_run=False)
    return {"fix_id": fix_id, "status": "applied", "detail": f"Applied safe fix: {fix_id}."}


def apply_safe_health_fixes(
    center: dict,
    *,
    dry_run: bool = True,
    handlers: dict[str, Callable[[], Any]] | None = None,
    event_recorder: EventRecorder = record_runtime_event,
) -> dict[str, Any]:
    """Apply or dry-run every safe fix currently exposed by the health center."""

    results = []
    for check in center.get("checks", []):
        plan = check.get("fix_plan", {})
        if plan.get("available") and plan.get("fix_id"):
            results.append(apply_health_fix(plan["fix_id"], dry_run=dry_run, handlers=handlers, event_recorder=event_recorder))
    return {"dry_run": dry_run, "count": len(results), "results": results}
