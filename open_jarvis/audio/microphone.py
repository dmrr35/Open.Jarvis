"""Microphone diagnostics that are safe to test without real hardware."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from open_jarvis.audio.voice_calibration import build_calibration_recommendation

Probe = Callable[[], bool]


def _default_microphone_probe() -> bool:
    try:
        import speech_recognition as sr

        return bool(sr.Microphone.list_microphone_names())
    except (ImportError, OSError, RuntimeError, ValueError):
        return False


def microphone_available(probe: Probe | None = None) -> bool:
    try:
        return bool((probe or _default_microphone_probe)())
    except (OSError, RuntimeError, ValueError, ImportError):
        return False


def build_microphone_status(probe: Probe | None = None) -> dict[str, object]:
    available = microphone_available(probe)
    return {
        "available": available,
        "status": "ready" if available else "unavailable",
        "message": "[INFO] Microphone ready." if available else "[WARN] Microphone unavailable. Voice input disabled.",
    }


def build_voice_calibration_status(samples: Iterable[float], *, safety_margin: int = 100) -> dict[str, object]:
    return dict(build_calibration_recommendation(list(samples), safety_margin=safety_margin))
