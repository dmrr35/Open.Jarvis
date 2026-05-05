"""TTS provider selection for JARVIS."""

from __future__ import annotations

from collections.abc import Mapping

_PROVIDERS = (
    {
        "id": "edge",
        "name": "Edge TTS",
        "available": True,
        "quality": "Online neural voices",
        "latency": "low",
        "setup": "Included through the edge-tts runtime dependency.",
    },
    {
        "id": "piper",
        "name": "Piper",
        "available": False,
        "quality": "Offline local voices",
        "latency": "low",
        "setup": "Install Piper locally and set JARVIS_TTS_PROVIDER=piper.",
    },
    {
        "id": "elevenlabs",
        "name": "ElevenLabs",
        "available": False,
        "quality": "Premium cloud voices",
        "latency": "medium",
        "setup": "Add an ElevenLabs API key and set JARVIS_TTS_PROVIDER=elevenlabs.",
    },
)


def build_tts_provider_options() -> list[dict[str, object]]:
    """Return the supported TTS providers for settings and onboarding UIs."""

    return [dict(provider) for provider in _PROVIDERS]


def select_tts_provider(env: Mapping[str, str] | None = None) -> dict[str, object]:
    """Select a provider from environment-style settings, falling back to Edge TTS."""

    provider_id = (env or {}).get("JARVIS_TTS_PROVIDER", "edge").strip().lower() or "edge"
    providers = {str(provider["id"]): dict(provider) for provider in _PROVIDERS}
    selected = providers.get(provider_id, providers["edge"])
    if selected["id"] != provider_id:
        selected["fallback_reason"] = f"Unknown provider '{provider_id}', using Edge TTS."
    return selected
