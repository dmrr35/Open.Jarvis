"""Actionable onboarding checks for first-run setup."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_STEPS: tuple[dict[str, Any], ...] = (
    {
        "id": "groq",
        "title": "Groq AI",
        "keys": ("GROQ_API_KEY",),
        "optional": False,
        "fix": "Add GROQ_API_KEY to your .env file.",
    },
    {
        "id": "spotify",
        "title": "Spotify",
        "keys": ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"),
        "optional": False,
        "fix": "Fill in SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.",
    },
    {
        "id": "gemini",
        "title": "Gemini",
        "keys": ("GEMINI_API_KEY",),
        "optional": True,
        "fix": "Add GEMINI_API_KEY only if you want Gemini-backed workflows.",
    },
    {
        "id": "microphone",
        "title": "Microphone calibration",
        "keys": ("JARVIS_ENERGY_THRESHOLD",),
        "optional": False,
        "fix": "Tune JARVIS_ENERGY_THRESHOLD for your room.",
    },
)


def _has_value(env: Mapping[str, str], key: str) -> bool:
    return bool(str(env.get(key, "")).strip())


def build_fix_command(keys: tuple[str, ...]) -> str:
    """Return a Windows-friendly command skeleton for missing setup values."""

    return " && ".join(f"setx {key} <value>" for key in keys)


def build_onboarding_result(env: Mapping[str, str] | None = None) -> dict:
    """Build a first-run checklist with testable statuses and fix commands."""

    env = env or {}
    steps = []
    for step in REQUIRED_STEPS:
        ready = all(_has_value(env, key) for key in step["keys"])
        status = "ready" if ready else "optional" if step["optional"] else "needs_setup"
        steps.append(
            {
                "id": step["id"],
                "title": step["title"],
                "status": status,
                "fix": step["fix"],
                "fix_command": "" if ready else build_fix_command(step["keys"]),
            }
        )

    return {
        "steps": steps,
        "summary": {
            "ready": sum(1 for step in steps if step["status"] == "ready"),
            "needs_setup": sum(1 for step in steps if step["status"] == "needs_setup"),
            "optional": sum(1 for step in steps if step["status"] == "optional"),
        },
    }
