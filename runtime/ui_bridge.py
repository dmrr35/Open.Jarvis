"""UI bridge helpers for runtime log callbacks."""

from __future__ import annotations

from jarvis_logging import get_logger
from observability import record_runtime_event

logger = get_logger("main")
_ui_callback = None


def set_ui_callback(fn):
    global _ui_callback
    _ui_callback = fn
    logger.info("UI callback registered.")


def _severity_from_message(message: str) -> str:
    lowered = message.lower()
    if "[error]" in lowered or "error" in lowered or "failed" in lowered:
        return "error"
    if "[warn]" in lowered or "warning" in lowered:
        return "warning"
    return "info"


def _notify_ui(message: str) -> None:
    if _ui_callback:
        try:
            _ui_callback(message)
        except (RuntimeError, ValueError, TypeError):
            logger.warning("UI callback failed while handling runtime message.", exc_info=True)


def _record(record_event, event_type: str, detail: str, severity: str, context: dict) -> None:
    try:
        record_event(event_type, detail, severity, context)
    except TypeError:
        record_event({"event_type": event_type, "detail": detail, "severity": severity, "context": context})


def send_log(message, *, record_event=record_runtime_event):
    """Send a log line to the UI and mirror it into structured runtime events."""

    _notify_ui(message)
    _record(record_event, "ui_log", message, _severity_from_message(message), {"source": "ui_bridge"})


def send_state(state: str, detail: str = "", *, record_event=record_runtime_event) -> None:
    """Publish an assistant state transition to the UI and event stream."""

    normalized_state = state.strip().upper()
    message = f"[STATE] {normalized_state}" + (f" - {detail}" if detail else "")
    _notify_ui(message)
    _record(record_event, "ui_state", detail or normalized_state, _severity_from_message(message), {"state": normalized_state})


def send_metric(name: str, value, *, unit: str = "", publish: bool = False, record_event=record_runtime_event) -> None:
    """Record a live UI metric and optionally publish it to the terminal stream."""

    metric_name = str(name).strip().lower()
    message = f"[METRIC] {metric_name}={value}{unit}"
    if publish:
        _notify_ui(message)
    _record(record_event, "ui_metric", message, "info", {"metric": metric_name, "value": value, "unit": unit})
