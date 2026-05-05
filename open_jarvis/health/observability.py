"""Minimal runtime observability helpers for JARVIS."""

from __future__ import annotations

import datetime as _dt
import json
from json import JSONDecodeError
from pathlib import Path

from open_jarvis.memory.privacy_mode import mask_sensitive_text, mask_sensitive_value

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
EVENT_LOG = LOG_DIR / "runtime_events.jsonl"
LOG_READ_CHUNK_SIZE = 8192


def record_runtime_event(event_type: str, detail: str, severity: str = "info", context: dict | None = None) -> None:
    """Append a structured runtime event."""

    payload = {
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        "event_type": event_type,
        "severity": severity,
        "detail": mask_sensitive_text(detail),
        "context": mask_sensitive_value(context or {}),
    }
    with open(EVENT_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def record_latency_metric(stage: str, latency_ms: float, **context) -> None:
    """Append a latency measurement as a structured runtime event."""

    metric_context = {"stage": stage, "latency_ms": round(float(latency_ms), 2)}
    metric_context.update(context)
    record_runtime_event("latency_metric", f"{stage} completed in {metric_context['latency_ms']} ms", "info", metric_context)


def _iter_recent_log_lines(limit: int) -> list[str]:
    """Read recent JSONL rows from the end of the runtime log."""

    if limit <= 0 or not EVENT_LOG.exists():
        return []

    lines: list[bytes] = []
    with open(EVENT_LOG, "rb") as handle:
        handle.seek(0, 2)
        position = handle.tell()
        remainder = b""
        while position > 0 and len(lines) < limit:
            read_size = min(LOG_READ_CHUNK_SIZE, position)
            position -= read_size
            handle.seek(position)
            chunk = handle.read(read_size) + remainder
            parts = chunk.split(b"\n")
            if position > 0:
                remainder = parts[0]
                parts = parts[1:]
            else:
                remainder = b""
            lines.extend(part for part in reversed(parts) if part.strip())
        if remainder.strip() and len(lines) < limit:
            lines.append(remainder)

    return [line.decode("utf-8", errors="ignore") for line in reversed(lines[:limit])]


def read_runtime_events(limit: int = 50) -> list[dict]:
    """Read the most recent runtime events."""

    if limit <= 0 or not EVENT_LOG.exists():
        return []

    events: list[dict] = []
    read_limit = max(limit, limit * 3)
    while len(events) < limit:
        events = []
        for line in _iter_recent_log_lines(read_limit):
            try:
                events.append(json.loads(line))
            except JSONDecodeError:
                continue
        if len(events) >= limit or read_limit > limit * 64:
            break
        read_limit *= 2
    return events[-limit:]


def format_runtime_event(event: dict) -> str:
    """Format a single runtime event for UI display."""

    timestamp = event.get("timestamp", "unknown-time")
    severity = str(event.get("severity", "info")).upper()
    event_type = event.get("event_type", "event")
    detail = event.get("detail", "")
    context = event.get("context") or {}

    lines = [f"[{severity}] {timestamp} | {event_type}"]
    if detail:
        lines.append(f"  {detail}")
    if context:
        context_bits = ", ".join(f"{key}={value}" for key, value in context.items())
        lines.append(f"  context: {context_bits}")
    return "\n".join(lines)


def _normalise_severity_filter(severity: str | None) -> str | None:
    if severity is None:
        return None
    severity = str(severity).strip().lower()
    if severity in {"", "all"}:
        return None
    return severity


def build_runtime_event_snapshot(limit: int = 25, severity: str | None = None) -> dict:
    """Return a compact summary of recent runtime events for UI viewers."""

    events = read_runtime_events(limit=limit)
    selected_severity = _normalise_severity_filter(severity)
    if selected_severity is not None:
        events = [event for event in events if str(event.get("severity", "")).lower() == selected_severity]
    report = build_slo_report(events)
    formatted_events = [format_runtime_event(event) for event in reversed(events)]
    filter_label = selected_severity or "all"
    return {
        "events": events,
        "report": report,
        "formatted_events": formatted_events,
        "summary": f"{report['status']} | {report['events_seen']} events | {report['warning_count']} warnings | {report['error_count']} errors | filter={filter_label}",
    }


def build_slo_report(events: list[dict] | None = None) -> dict:
    """Summarize recent runtime posture."""

    events = read_runtime_events() if events is None else events
    errors = [event for event in events if event.get("severity") in {"error", "critical"}]
    warnings = [event for event in events if event.get("severity") == "warning"]
    uptime_hint = len(events)

    if errors:
        status = "degraded"
        recommendation = "Review recent runtime errors and narrow the failing command path."
    elif warnings:
        status = "watch"
        recommendation = "Warnings are present. Keep an eye on the next session."
    else:
        status = "healthy"
        recommendation = "Runtime posture looks stable."

    return {
        "status": status,
        "events_seen": uptime_hint,
        "warning_count": len(warnings),
        "error_count": len(errors),
        "recommendation": recommendation,
    }


def build_latency_snapshot(limit: int = 25) -> dict:
    """Return recent latency metrics for cockpit/status surfaces."""

    events = [event for event in read_runtime_events(limit=limit) if event.get("event_type") == "latency_metric"]
    latencies = [
        float(event.get("context", {}).get("latency_ms", 0))
        for event in events
        if isinstance(event.get("context", {}).get("latency_ms", 0), int | float)
    ]
    average = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    return {
        "count": len(events),
        "average_ms": average,
        "latest": events[-1] if events else None,
    }
