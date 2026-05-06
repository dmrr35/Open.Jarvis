"""Wake-word configuration and matching without microphone dependencies."""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass

_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}


def parse_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return default


def normalize_voice_phrase(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", " ", text.lower())
    return " ".join(normalized.split())


@dataclass(frozen=True)
class WakeWordConfig:
    wake_word: str = "jarvis"
    enabled: bool = True
    voice_enabled: bool = True
    cooldown_seconds: float = 1.0


def build_wake_word_config(env: Mapping[str, str] | None = None) -> dict[str, object]:
    source = os.environ if env is None else env
    wake_word = normalize_voice_phrase(source.get("JARVIS_WAKE_WORD", "jarvis")) or "jarvis"
    voice_enabled = parse_bool(source.get("JARVIS_VOICE_ENABLED"), True)
    enabled = parse_bool(source.get("JARVIS_WAKE_WORD_ENABLED"), True) and voice_enabled
    try:
        cooldown_seconds = max(0.0, float(source.get("JARVIS_WAKE_WORD_COOLDOWN_SECONDS", "1.0")))
    except (TypeError, ValueError):
        cooldown_seconds = 1.0
    return {
        "wake_word": wake_word,
        "enabled": enabled,
        "voice_enabled": voice_enabled,
        "cooldown_seconds": cooldown_seconds,
    }


def _config_value(config: WakeWordConfig | Mapping[str, object] | None, key: str, default: object) -> object:
    if config is None:
        return default
    if isinstance(config, WakeWordConfig):
        return getattr(config, key)
    return config.get(key, default)


def wake_word_detected(
    text: str,
    *,
    wake_word: str | None = None,
    config: WakeWordConfig | Mapping[str, object] | None = None,
    now: float | None = None,
    last_detected_at: float | None = None,
) -> bool:
    result = analyze_wake_word(text, wake_word=wake_word, config=config, now=now, last_detected_at=last_detected_at)
    return bool(result["detected"])


def analyze_wake_word(
    text: str,
    *,
    wake_word: str | None = None,
    config: WakeWordConfig | Mapping[str, object] | None = None,
    now: float | None = None,
    last_detected_at: float | None = None,
) -> dict[str, object]:
    configured_word = normalize_voice_phrase(wake_word or str(_config_value(config, "wake_word", "jarvis"))) or "jarvis"
    enabled = bool(_config_value(config, "enabled", True))
    cooldown_seconds = float(_config_value(config, "cooldown_seconds", 0.0))
    normalized_text = normalize_voice_phrase(text)
    cooldown_active = False
    if not enabled:
        return {
            "detected": False,
            "enabled": False,
            "wake_word": configured_word,
            "normalized": normalized_text,
            "reason": "wake word disabled",
            "cooldown_active": False,
        }
    if last_detected_at is not None and now is not None and now - last_detected_at < cooldown_seconds:
        cooldown_active = True
    tokens = normalized_text.split()
    wake_tokens = configured_word.split()
    detected = False
    if wake_tokens and len(tokens) >= len(wake_tokens) and not cooldown_active:
        detected = any(tokens[index : index + len(wake_tokens)] == wake_tokens for index in range(len(tokens) - len(wake_tokens) + 1))
    return {
        "detected": detected,
        "enabled": enabled,
        "wake_word": configured_word,
        "normalized": normalized_text,
        "reason": "detected" if detected else ("cooldown active" if cooldown_active else "not detected"),
        "cooldown_active": cooldown_active,
    }


class WakeWordDetector:
    def __init__(self, wake_word: str = "jarvis", *, enabled: bool = True, cooldown_seconds: float = 1.0, clock: Callable[[], float] | None = None) -> None:
        self.config = WakeWordConfig(wake_word=normalize_voice_phrase(wake_word) or "jarvis", enabled=enabled, cooldown_seconds=max(0.0, cooldown_seconds))
        self.clock = clock or time.monotonic
        self.last_detected_at: float | None = None

    def detect(self, text: str) -> dict[str, object]:
        now = self.clock()
        result = analyze_wake_word(text, config=self.config, now=now, last_detected_at=self.last_detected_at)
        if result["detected"]:
            self.last_detected_at = now
        return result
