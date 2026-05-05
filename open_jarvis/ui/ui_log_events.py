"""Structured terminal event formatting for the JARVIS cockpit UI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LogEvent:
    """One normalized command stream event."""

    kind: str
    prefix: str
    message: str
    color: str


EVENT_COLORS = {
    "info": "#8FB7C8",
    "voice": "#00D7FF",
    "cmd": "#D8F6FF",
    "task": "#4CEBFF",
    "ok": "#00FFC6",
    "warn": "#FFC857",
    "error": "#FF4D6D",
}

EVENT_PREFIXES = {
    "info": "[INFO]",
    "voice": "[VOICE]",
    "cmd": "[CMD]",
    "task": "[TASK]",
    "ok": "[OK]",
    "warn": "[WARN]",
    "error": "[ERROR]",
}

LEGACY_KIND_MAP = {
    "system": "info",
    "jarvis": "ok",
    "user": "cmd",
    "error": "error",
    "voice": "voice",
    "task": "task",
    "ok": "ok",
    "warn": "warn",
    "info": "info",
    "cmd": "cmd",
}


def normalize_log_event(message: str, kind: str = "info") -> LogEvent:
    """Return a display-ready event with prefix and color."""

    normalized_kind = LEGACY_KIND_MAP.get(kind.lower(), "info")
    clean_message = message.strip()
    prefix = EVENT_PREFIXES[normalized_kind]
    if clean_message.startswith("[") and "]" in clean_message[:12]:
        display_message = clean_message
    else:
        display_message = f"{prefix} {clean_message}"
    return LogEvent(
        kind=normalized_kind,
        prefix=prefix,
        message=display_message,
        color=EVENT_COLORS[normalized_kind],
    )


def infer_log_kind(message: str) -> str:
    """Infer a terminal event kind from a runtime callback message."""

    lowered = message.lower()
    if "error" in lowered or "failed" in lowered:
        return "error"
    if "listening" in lowered or "voice" in lowered or "wake word detected" in lowered:
        return "voice"
    if "you:" in lowered:
        return "cmd"
    if "analysis" in lowered or "processing" in lowered or "routing" in lowered or "launching" in lowered or "executing" in lowered:
        return "task"
    if "jarvis:" in lowered or "success" in lowered or "ready" in lowered or "completed" in lowered:
        return "ok"
    return "info"
