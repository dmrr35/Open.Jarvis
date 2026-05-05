"""Offline-first profile planning for local STT, TTS, and LLM operation."""

from __future__ import annotations

from collections.abc import Mapping


def build_offline_profile(env: Mapping[str, str] | None = None) -> dict:
    """Describe whether JARVIS can run core AI/voice flows locally."""

    env = env or {}
    stt_enabled = str(env.get("JARVIS_OFFLINE_STT", "0")).lower() in {"1", "true", "yes", "on"}
    tts_provider = env.get("JARVIS_TTS_PROVIDER", "edge").lower()
    local_llm = env.get("JARVIS_LOCAL_LLM_URL", "").strip()
    components = [
        {
            "id": "stt",
            "name": "Speech to text",
            "local": stt_enabled,
            "status": "ready" if stt_enabled else "needs_setup",
            "fix": "Set JARVIS_OFFLINE_STT=1 and configure JARVIS_VOSK_MODEL_PATH.",
        },
        {
            "id": "tts",
            "name": "Text to speech",
            "local": tts_provider == "piper",
            "status": "ready" if tts_provider == "piper" else "cloud",
            "fix": "Install Piper and set JARVIS_TTS_PROVIDER=piper for fully local speech output.",
        },
        {
            "id": "llm",
            "name": "Language model",
            "local": bool(local_llm),
            "status": "ready" if local_llm else "needs_setup",
            "fix": "Set JARVIS_LOCAL_LLM_URL to a local Ollama or LM Studio endpoint.",
        },
    ]
    ready = all(component["local"] for component in components)
    return {
        "status": "ready" if ready else "partial",
        "components": components,
        "summary": {
            "local_components": sum(1 for component in components if component["local"]),
            "total_components": len(components),
        },
    }
