"""Shared setup, onboarding and health helpers for Open.Jarvis."""

from __future__ import annotations

import datetime as _dt
import json
import os
from collections.abc import Iterable
from pathlib import Path

from jarvis_admin_config import KNOWN_LIMITATIONS, MANAGED_ENV_KEYS, SETTINGS_GUIDE
from speech_backend import offline_stt_available, recognition_mode

REPO_ROOT = Path(__file__).resolve().parent
SETUP_STATE_FILE = REPO_ROOT / "jarvis_setup.json"
ENV_FILE = REPO_ROOT / ".env"


def format_actionable_message(title: str, why: str, fix: str) -> str:
    """Render a user-facing message with a clear cause and next step."""

    return f"{title}\nReason: {why}\nNext step: {fix}"


def _env(env: dict | None = None) -> dict:
    return dict(os.environ if env is None else env)


def _has_value(env: dict, key: str) -> bool:
    value = env.get(key)
    return value is not None and str(value).strip() != ""


def _default_package_checker(name: str):
    return __import__(name)


def build_settings_guide() -> list[dict]:
    """Return a copy of the settings guide with safe defaults and descriptions."""

    return [dict(item) for item in SETTINGS_GUIDE]


def build_known_limitations() -> list[dict]:
    """Return known limitations together with their planned fixes."""

    return [dict(item) for item in KNOWN_LIMITATIONS]


def build_env_template() -> str:
    """Return a recommended .env template for onboarding and docs."""

    lines = [
        "# JARVIS recommended local setup",
        "GROQ_API_KEY=",
        "SPOTIFY_CLIENT_ID=",
        "SPOTIFY_CLIENT_SECRET=",
        "SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback",
        "GEMINI_API_KEY=",
        "JARVIS_WAKE_WORD=jarvis",
        "JARVIS_ACTIVE_TIMEOUT=60",
        "JARVIS_ACTION_SEQUENCE_DELAY=0.1",
        "JARVIS_APP_LAUNCH_DELAY=0.2",
        "JARVIS_CPU_SAMPLE_INTERVAL=0.1",
        "JARVIS_SCREENSHOT_DELAY=0.2",
        "JARVIS_SLEEP_ACTION_DELAY=1.0",
        "JARVIS_TYPE_DELAY=0.1",
        "JARVIS_ENERGY_THRESHOLD=300",
        "JARVIS_PAUSE_THRESHOLD=1.0",
        "JARVIS_TTS_PROVIDER=edge",
        "JARVIS_OFFLINE_STT=1",
        "JARVIS_VOSK_MODEL_PATH=",
        "JARVIS_RELEASE_SIGNING_KEY=",
        "JARVIS_LOCAL_LLM_URL=",
        "JARVIS_PERMISSION_PROFILE=normal",
        "JARVIS_PRIVACY_MODE=false",
    ]
    return "\n".join(lines)


def read_env_settings(path: Path | None = None) -> dict:
    """Read managed env settings from .env style files."""

    path = path or ENV_FILE
    data = {key: "" for key in MANAGED_ENV_KEYS}
    if not path.exists():
        return data

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in data:
            data[key] = value.strip()
    return data


def write_env_settings(settings: dict, path: Path | None = None) -> Path:
    """Write managed env settings back to disk."""

    path = path or ENV_FILE
    current = read_env_settings(path)
    current.update({key: str(value).strip() for key, value in settings.items() if key in current})

    lines = ["# JARVIS managed settings"]
    for key in MANAGED_ENV_KEYS:
        lines.append(f"{key}={current.get(key, '')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_onboarding_steps(env: dict | None = None) -> list[dict]:
    """Build the onboarding checklist with simple status values."""

    env = _env(env)
    groq_ready = _has_value(env, "GROQ_API_KEY")
    spotify_ready = _has_value(env, "SPOTIFY_CLIENT_ID") and _has_value(env, "SPOTIFY_CLIENT_SECRET")
    gemini_ready = _has_value(env, "GEMINI_API_KEY")
    mic_ready = _has_value(env, "JARVIS_ENERGY_THRESHOLD")
    tts_provider = env.get("JARVIS_TTS_PROVIDER", "edge").strip() or "edge"

    return [
        {
            "id": "groq",
            "title": "Groq AI",
            "status": "ready" if groq_ready else "needs_setup",
            "detail": "Required for AI command routing and summarization.",
            "fix": "Add GROQ_API_KEY to your .env file and restart the app.",
        },
        {
            "id": "spotify",
            "title": "Spotify",
            "status": "ready" if spotify_ready else "needs_setup",
            "detail": "Required for music playback and search control.",
            "fix": "Fill SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file.",
        },
        {
            "id": "gemini",
            "title": "Gemini",
            "status": "ready" if gemini_ready else "optional",
            "detail": "Optional today, ready for future assistant flows.",
            "fix": "Add GEMINI_API_KEY to your .env file if you want to enable it.",
        },
        {
            "id": "mic",
            "title": "Microphone calibration",
            "status": "ready" if mic_ready else "needs_setup",
            "detail": "Room sensitivity matters for reliable voice activation.",
            "fix": "Start with JARVIS_ENERGY_THRESHOLD=300 and adjust it for your room.",
        },
        {
            "id": "tts",
            "title": "Voice output provider",
            "status": "ready",
            "detail": f"Current provider: {tts_provider}. Edge TTS is the safe default.",
            "fix": "Keep JARVIS_TTS_PROVIDER=edge unless you install another provider.",
        },
    ]


def build_health_checks(env: dict | None = None, file_exists=None, package_checker=None) -> list[dict]:
    """Build a prioritized health report."""

    env = _env(env)
    if file_exists is None:
        file_exists = os.path.exists
    if package_checker is None:
        package_checker = _default_package_checker

    checks = []

    groq_ready = _has_value(env, "GROQ_API_KEY")
    checks.append(
        {
            "id": "groq_api",
            "severity": "ok" if groq_ready else "warning",
            "title": "Groq AI credentials",
            "detail": "AI command routing is ready." if groq_ready else "Groq cloud routing is disabled; local rule commands still work.",
            "fix": "Add GROQ_API_KEY to your .env file only if you want cloud AI routing.",
            "fix_command": "notepad .env",
        }
    )

    spotify_ready = _has_value(env, "SPOTIFY_CLIENT_ID") and _has_value(env, "SPOTIFY_CLIENT_SECRET")
    checks.append(
        {
            "id": "spotify",
            "severity": "ok" if spotify_ready else "warning",
            "title": "Spotify integration",
            "detail": "Spotify control is ready." if spotify_ready else "Spotify credentials are missing.",
            "fix": "Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.",
            "fix_command": "notepad .env",
        }
    )

    gemini_ready = _has_value(env, "GEMINI_API_KEY")
    checks.append(
        {
            "id": "gemini",
            "severity": "info",
            "title": "Gemini integration",
            "detail": "Gemini key is present." if gemini_ready else "Gemini is optional and can stay empty.",
            "fix": "Add GEMINI_API_KEY only if you need Gemini-backed flows.",
            "fix_command": "notepad .env",
        }
    )

    wake_word = env.get("JARVIS_WAKE_WORD", "jarvis").strip()
    checks.append(
        {
            "id": "wake_word",
            "severity": "ok" if wake_word else "warning",
            "title": "Wake word",
            "detail": f"Current wake word: {wake_word or 'unset'}",
            "fix": "Keep JARVIS_WAKE_WORD short, unique, and easy to say.",
            "fix_command": "notepad .env",
        }
    )

    mic_threshold = env.get("JARVIS_ENERGY_THRESHOLD", "").strip()
    checks.append(
        {
            "id": "microphone",
            "severity": "ok" if mic_threshold else "warning",
            "title": "Microphone calibration",
            "detail": "Energy threshold is set." if mic_threshold else "Microphone sensitivity is still using a default path.",
            "fix": "Calibrate JARVIS_ENERGY_THRESHOLD for your room.",
            "fix_command": "notepad .env",
        }
    )

    tts_provider = env.get("JARVIS_TTS_PROVIDER", "edge").strip() or "edge"
    checks.append(
        {
            "id": "tts_provider",
            "severity": "ok" if tts_provider in {"edge", "piper", "elevenlabs"} else "warning",
            "title": "TTS provider",
            "detail": f"Current provider: {tts_provider}.",
            "fix": "Use JARVIS_TTS_PROVIDER=edge unless another provider is installed.",
            "fix_command": "notepad .env",
        }
    )

    checks.append(
        {
            "id": "setup_state",
            "severity": "info" if file_exists(SETUP_STATE_FILE) else "warning",
            "title": "Onboarding completion",
            "detail": "Setup state file exists." if file_exists(SETUP_STATE_FILE) else "First-run setup does not look complete yet.",
            "fix": "Complete the onboarding wizard and save the configuration.",
            "fix_command": "python arayuz.py",
        }
    )

    offline_requested = str(env.get("JARVIS_OFFLINE_STT", "0")).strip() in {"1", "true", "yes", "on"}
    offline_available = offline_stt_available()
    checks.append(
        {
            "id": "offline_stt",
            "severity": "ok" if offline_available else "warning" if offline_requested else "info",
            "title": "Offline speech fallback",
            "detail": f"Recognition mode: {recognition_mode()}." if offline_requested else "Offline fallback disabled by default.",
            "fix": "Set JARVIS_OFFLINE_STT=1 and point JARVIS_VOSK_MODEL_PATH to a local model if you want degraded-mode transcription.",
            "fix_command": "notepad .env",
        }
    )

    try:
        package_checker("speech_recognition")
        package_checker("customtkinter")
        package_checker("psutil")
        checks.append(
            {
                "id": "packages",
                "severity": "ok",
                "title": "Core Python packages",
                "detail": "Core runtime packages are installed.",
                "fix": "No missing package action is needed.",
                "fix_command": "python -m pip check",
            }
        )
    except ImportError:
        checks.append(
            {
                "id": "packages",
                "severity": "critical",
                "title": "Core Python packages",
                "detail": "At least one required Python runtime package is missing.",
                "fix": "Install the runtime dependencies from requirements.txt.",
                "fix_command": "python -m pip install -r requirements.txt",
            }
        )

    return checks


def render_health_report(checks: Iterable[dict]) -> str:
    """Format health checks into a readable console report."""

    severity_labels = {
        "critical": "CRITICAL",
        "warning": "WARNING",
        "info": "INFO",
        "ok": "OK",
    }
    lines = []
    for item in checks:
        label = severity_labels.get(item.get("severity", "info"), "INFO")
        lines.append(f"[{label}] {item.get('title', item.get('id', 'check'))}")
        detail = item.get("detail")
        if detail:
            lines.append(f"  {detail}")
        fix = item.get("fix")
        if fix:
            lines.append(f"  Fix: {fix}")
        fix_command = item.get("fix_command")
        if fix_command:
            lines.append(f"  Fix command: {fix_command}")
    return "\n".join(lines)


def save_setup_state(payload: dict | None = None) -> Path:
    """Persist onboarding completion state."""

    data = {
        "completed": True,
        "completed_at": _dt.datetime.now().isoformat(timespec="seconds"),
    }
    if payload:
        data.update(payload)
    SETUP_STATE_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return SETUP_STATE_FILE


def should_show_onboarding() -> bool:
    """Return True when the onboarding wizard should be shown."""

    if not SETUP_STATE_FILE.exists():
        return True
    try:
        content = SETUP_STATE_FILE.read_text(encoding="utf-8").strip()
        return content == ""
    except OSError:
        return True
