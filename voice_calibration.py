"""Microphone calibration helpers for first-run setup."""

from __future__ import annotations

from statistics import median


def build_calibration_recommendation(samples: list[int | float], safety_margin: int = 100) -> dict:
    """Recommend a speech-recognition energy threshold from ambient noise samples."""

    clean_samples = [max(0, int(sample)) for sample in samples]
    if not clean_samples:
        return {
            "status": "needs_samples",
            "recommended_threshold": 300,
            "env_line": "JARVIS_ENERGY_THRESHOLD=300",
            "detail": "No samples were provided; keep the safe default.",
        }
    baseline = int(median(clean_samples))
    peak = max(clean_samples)
    recommended = baseline + int(safety_margin)
    return {
        "status": "ready",
        "baseline": baseline,
        "peak": peak,
        "recommended_threshold": recommended,
        "env_line": f"JARVIS_ENERGY_THRESHOLD={recommended}",
        "detail": "Use this value as a starting point, then rerun calibration if the room changes.",
    }
