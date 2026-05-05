"""Static admin settings catalogs for JARVIS."""

from __future__ import annotations

MANAGED_ENV_KEYS = [
    "JARVIS_WAKE_WORD",
    "JARVIS_ACTIVE_TIMEOUT",
    "JARVIS_ACTION_SEQUENCE_DELAY",
    "JARVIS_APP_LAUNCH_DELAY",
    "JARVIS_CPU_SAMPLE_INTERVAL",
    "JARVIS_SCREENSHOT_DELAY",
    "JARVIS_SLEEP_ACTION_DELAY",
    "JARVIS_TYPE_DELAY",
    "JARVIS_ENERGY_THRESHOLD",
    "JARVIS_PAUSE_THRESHOLD",
    "JARVIS_TTS_PROVIDER",
    "JARVIS_OFFLINE_STT",
    "JARVIS_VOSK_MODEL_PATH",
    "JARVIS_RELEASE_SIGNING_KEY",
    "JARVIS_LOCAL_LLM_URL",
    "JARVIS_PERMISSION_PROFILE",
    "JARVIS_PRIVACY_MODE",
    "GROQ_API_KEY",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_REDIRECT_URI",
    "GEMINI_API_KEY",
]


SETTINGS_GUIDE = [
    {
        "key": "JARVIS_WAKE_WORD",
        "default": "jarvis",
        "safe_default": "jarvis",
        "description": "Wake word used to activate JARVIS. Safe default: keep it short, unique, and easy to say.",
    },
    {
        "key": "JARVIS_ACTIVE_TIMEOUT",
        "default": "60",
        "safe_default": "60",
        "description": "Seconds JARVIS stays actively listening after wake-up before returning to standby.",
    },
    {
        "key": "JARVIS_ACTION_SEQUENCE_DELAY",
        "default": "0.1",
        "safe_default": "0.1",
        "description": "Short pause between multi-step desktop actions. Lower values make workflows faster.",
    },
    {
        "key": "JARVIS_APP_LAUNCH_DELAY",
        "default": "0.2",
        "safe_default": "0.2",
        "description": "Stabilization pause after launching an app. Increase this on slower machines.",
    },
    {
        "key": "JARVIS_CPU_SAMPLE_INTERVAL",
        "default": "0.1",
        "safe_default": "0.1",
        "description": "CPU sampling duration for quick system checks.",
    },
    {
        "key": "JARVIS_SCREENSHOT_DELAY",
        "default": "0.2",
        "safe_default": "0.2",
        "description": "Short delay before taking screenshots so the desktop can settle.",
    },
    {
        "key": "JARVIS_SLEEP_ACTION_DELAY",
        "default": "1.0",
        "safe_default": "1.0",
        "description": "Final delay before sleep-related desktop actions.",
    },
    {
        "key": "JARVIS_TYPE_DELAY",
        "default": "0.1",
        "safe_default": "0.1",
        "description": "Pause before automatic typing begins.",
    },
    {
        "key": "JARVIS_ENERGY_THRESHOLD",
        "default": "300",
        "safe_default": "300",
        "description": "Microphone sensitivity. Safe default: start at 300, then calibrate for your room.",
    },
    {
        "key": "JARVIS_PAUSE_THRESHOLD",
        "default": "1.0",
        "safe_default": "1.0",
        "description": "Silence duration used to decide when a spoken command has ended.",
    },
    {
        "key": "JARVIS_TTS_PROVIDER",
        "default": "edge",
        "safe_default": "edge",
        "description": "Voice output provider. Edge is the safe default; Piper and premium cloud providers can be added later.",
    },
    {
        "key": "JARVIS_OFFLINE_STT",
        "default": "1",
        "safe_default": "1",
        "description": "Offline speech recognition fallback. Safe default: enabled when a Vosk model is available.",
    },
    {
        "key": "JARVIS_VOSK_MODEL_PATH",
        "default": "",
        "safe_default": "empty",
        "description": "Path to a local Vosk model. Leave empty until a model is installed.",
    },
    {
        "key": "JARVIS_RELEASE_SIGNING_KEY",
        "default": "",
        "safe_default": "empty",
        "description": "Release signing key. Keep empty locally unless you are running a trusted release flow.",
    },
    {
        "key": "JARVIS_LOCAL_LLM_URL",
        "default": "",
        "safe_default": "empty",
        "description": "Optional local LLM endpoint for degraded or offline command routing.",
    },
    {
        "key": "JARVIS_PERMISSION_PROFILE",
        "default": "normal",
        "safe_default": "safe",
        "description": "Runtime permission profile. Use safe for demos and normal for daily desktop use.",
    },
    {
        "key": "JARVIS_PRIVACY_MODE",
        "default": "false",
        "safe_default": "false",
        "description": "Privacy mode disables memory writes and tightens secret masking in user-visible output.",
    },
    {
        "key": "GROQ_API_KEY",
        "default": "",
        "safe_default": "empty",
        "description": "AI command routing key. Leave empty in public files and add it only to your local .env.",
    },
    {
        "key": "SPOTIFY_CLIENT_ID",
        "default": "",
        "safe_default": "empty",
        "description": "Spotify client ID for music control.",
    },
    {
        "key": "SPOTIFY_CLIENT_SECRET",
        "default": "",
        "safe_default": "empty",
        "description": "Spotify client secret for music control. Keep it local.",
    },
    {
        "key": "SPOTIFY_REDIRECT_URI",
        "default": "http://127.0.0.1:8888/callback",
        "safe_default": "http://127.0.0.1:8888/callback",
        "description": "Spotify OAuth callback URL. The localhost default is safe for development.",
    },
    {
        "key": "GEMINI_API_KEY",
        "default": "",
        "safe_default": "empty",
        "description": "Optional Gemini integration key for future assistant flows.",
    },
]


KNOWN_LIMITATIONS = [
    {
        "gap": "First-run setup still leaves some integrations to manual configuration.",
        "planned_solution": "Expand onboarding with Groq, Spotify, Gemini, microphone, privacy, and provider checks in one guided flow.",
        "priority": "high",
        "difficulty": "medium",
        "owner": "Product/Core",
        "target": "Medium roadmap",
    },
    {
        "gap": "Health output is useful but not yet a full in-app operations center.",
        "planned_solution": "Keep critical, warning, info, and ok grouping, then expose it in a dedicated Health Center UI.",
        "priority": "high",
        "difficulty": "medium",
        "owner": "Core/UI",
        "target": "Medium roadmap",
    },
    {
        "gap": "Settings are powerful, but their impact is not always obvious to first-time users.",
        "planned_solution": "Surface safe defaults, descriptions, and restart notes directly in the settings and onboarding screens.",
        "priority": "medium",
        "difficulty": "medium",
        "owner": "UI",
        "target": "Medium roadmap",
    },
    {
        "gap": "Microphone behavior depends heavily on the room and device.",
        "planned_solution": "Add calibration presets and saved profiles after the current guided threshold workflow.",
        "priority": "medium",
        "difficulty": "medium",
        "owner": "Voice",
        "target": "Medium roadmap",
    },
    {
        "gap": "Voice output currently defaults to Edge TTS without an explicit provider decision point.",
        "planned_solution": "Add a provider selector and prepare adapters for offline and premium voice engines.",
        "priority": "medium",
        "difficulty": "medium",
        "owner": "Voice/UI",
        "target": "Medium roadmap",
    },
]
