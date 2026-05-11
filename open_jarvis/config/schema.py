"""Typed configuration schema for non-secret Open.Jarvis settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldDefinition:
    key: str
    value_type: str
    default: Any
    env_var: str | None = None
    allowed_values: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    description: str = ""
    restart_required: bool = False

    @property
    def category(self) -> str:
        return self.key.split(".", 1)[0]

    @property
    def name(self) -> str:
        return self.key.split(".", 1)[1]


FIELD_DEFINITIONS: dict[str, FieldDefinition] = {
    "general.theme": FieldDefinition("general.theme", "string", "system", allowed_values=("system", "dark", "light")),
    "general.language": FieldDefinition("general.language", "string", "en"),
    "general.debug_mode": FieldDefinition("general.debug_mode", "bool", False),
    "general.start_minimized": FieldDefinition("general.start_minimized", "bool", False),
    "ai.mode": FieldDefinition(
        "ai.mode",
        "string",
        "auto",
        env_var="JARVIS_AI_MODE",
        allowed_values=("auto", "free_cloud", "offline", "rules", "local", "cloud"),
    ),
    "ai.groq_enabled": FieldDefinition("ai.groq_enabled", "bool", False, env_var="JARVIS_ENABLE_GROQ"),
    "ai.groq_model": FieldDefinition("ai.groq_model", "string", "llama-3.1-8b-instant", env_var="JARVIS_GROQ_MODEL"),
    "ai.local_llm_url": FieldDefinition("ai.local_llm_url", "string", "", env_var="JARVIS_LOCAL_LLM_URL"),
    "ai.cloud_fallback_enabled": FieldDefinition("ai.cloud_fallback_enabled", "bool", True),
    "voice.voice_enabled": FieldDefinition("voice.voice_enabled", "bool", True, env_var="JARVIS_VOICE_ENABLED", restart_required=True),
    "voice.wake_word": FieldDefinition("voice.wake_word", "string", "jarvis", env_var="JARVIS_WAKE_WORD", restart_required=True),
    "voice.wake_word_enabled": FieldDefinition("voice.wake_word_enabled", "bool", True, env_var="JARVIS_WAKE_WORD_ENABLED", restart_required=True),
    "voice.wake_word_cooldown_seconds": FieldDefinition(
        "voice.wake_word_cooldown_seconds",
        "float",
        1.0,
        env_var="JARVIS_WAKE_WORD_COOLDOWN_SECONDS",
        minimum=0.0,
        maximum=60.0,
    ),
    "voice.push_to_talk_enabled": FieldDefinition("voice.push_to_talk_enabled", "bool", True, env_var="JARVIS_PUSH_TO_TALK_ENABLED"),
    "voice.active_timeout": FieldDefinition("voice.active_timeout", "int", 60, env_var="JARVIS_ACTIVE_TIMEOUT", minimum=1, maximum=3600),
    "voice.energy_threshold": FieldDefinition("voice.energy_threshold", "int", 300, env_var="JARVIS_ENERGY_THRESHOLD", minimum=1, maximum=10000),
    "voice.pause_threshold": FieldDefinition("voice.pause_threshold", "float", 1.0, env_var="JARVIS_PAUSE_THRESHOLD", minimum=0.1, maximum=10.0),
    "voice.tts_enabled": FieldDefinition("voice.tts_enabled", "bool", True, env_var="JARVIS_TTS_ENABLED"),
    "voice.tts_provider": FieldDefinition("voice.tts_provider", "string", "edge", env_var="JARVIS_TTS_PROVIDER", allowed_values=("edge", "piper", "elevenlabs")),
    "voice.offline_stt_enabled": FieldDefinition("voice.offline_stt_enabled", "bool", True, env_var="JARVIS_OFFLINE_STT"),
    "voice.vosk_model_path": FieldDefinition("voice.vosk_model_path", "path", "", env_var="JARVIS_VOSK_MODEL_PATH"),
    "runtime.action_sequence_delay": FieldDefinition("runtime.action_sequence_delay", "float", 0.1, env_var="JARVIS_ACTION_SEQUENCE_DELAY", minimum=0.0),
    "runtime.app_launch_delay": FieldDefinition("runtime.app_launch_delay", "float", 0.2, env_var="JARVIS_APP_LAUNCH_DELAY", minimum=0.0),
    "runtime.cpu_sample_interval": FieldDefinition("runtime.cpu_sample_interval", "float", 0.1, env_var="JARVIS_CPU_SAMPLE_INTERVAL", minimum=0.0),
    "runtime.screenshot_delay": FieldDefinition("runtime.screenshot_delay", "float", 0.2, env_var="JARVIS_SCREENSHOT_DELAY", minimum=0.0),
    "runtime.sleep_action_delay": FieldDefinition("runtime.sleep_action_delay", "float", 1.0, env_var="JARVIS_SLEEP_ACTION_DELAY", minimum=0.0),
    "runtime.type_delay": FieldDefinition("runtime.type_delay", "float", 0.1, env_var="JARVIS_TYPE_DELAY", minimum=0.0),
    "runtime.allow_destructive_actions": FieldDefinition("runtime.allow_destructive_actions", "bool", False, env_var="JARVIS_ALLOW_DESTRUCTIVE_ACTIONS"),
    "plugins.enabled": FieldDefinition("plugins.enabled", "bool", True),
    "plugins.directory": FieldDefinition("plugins.directory", "path", "plugins"),
    "plugins.security_mode": FieldDefinition("plugins.security_mode", "string", "strict", allowed_values=("strict", "standard", "development")),
    "plugins.permission_profile": FieldDefinition(
        "plugins.permission_profile",
        "string",
        "normal",
        env_var="JARVIS_PERMISSION_PROFILE",
        allowed_values=("safe", "normal", "admin"),
    ),
    "spotify.enabled": FieldDefinition("spotify.enabled", "bool", False, env_var="JARVIS_ENABLE_SPOTIFY"),
    "spotify.redirect_uri": FieldDefinition("spotify.redirect_uri", "string", "http://127.0.0.1:8888/callback", env_var="SPOTIFY_REDIRECT_URI"),
    "privacy.memory_enabled": FieldDefinition("privacy.memory_enabled", "bool", True),
    "privacy.privacy_mode": FieldDefinition("privacy.privacy_mode", "bool", False, env_var="JARVIS_PRIVACY_MODE"),
    "privacy.log_level": FieldDefinition("privacy.log_level", "string", "info", allowed_values=("error", "warning", "info", "debug")),
}

ENV_TO_FIELD = {field.env_var: key for key, field in FIELD_DEFINITIONS.items() if field.env_var}


def get_field(key: str) -> FieldDefinition:
    return FIELD_DEFINITIONS[key]
