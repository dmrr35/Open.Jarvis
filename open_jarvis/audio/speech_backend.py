"""Speech recognition helpers with an optional offline Vosk fallback."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from json import JSONDecodeError
from pathlib import Path

import speech_recognition as sr


def _candidate_model_roots() -> list[Path]:
    candidates = []

    env_path = os.getenv("JARVIS_VOSK_MODEL_PATH") or os.getenv("VOSK_MODEL_PATH")
    if env_path:
        candidates.append(Path(env_path))

    home = Path.home()
    candidates.extend(
        [
            home / ".open_jarvis" / "vosk_models",
            home / ".open_jarvis" / "vosk_model",
            home / "AppData" / "Local" / "Open.Jarvis" / "vosk_models",
            Path(__file__).resolve().parent / "model",
            Path(__file__).resolve().parent / "models" / "vosk-model-small-en-us-0.15",
        ]
    )

    return candidates


def _looks_like_model(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    return any((path / marker).exists() for marker in ["am", "graph", "conf"])


def resolve_vosk_model_path() -> Path | None:
    """Resolve a usable Vosk model directory if one is available."""

    for root in _candidate_model_roots():
        if root.is_dir() and (root / "am").exists():
            return root
        if root.is_dir():
            for child in root.iterdir():
                if _looks_like_model(child):
                    return child
    return None


@lru_cache(maxsize=1)
def _load_vosk_model():
    model_path = resolve_vosk_model_path()
    if model_path is None:
        return None

    try:
        from vosk import Model

        return Model(str(model_path))
    except (ImportError, OSError, RuntimeError, ValueError):
        return None


def offline_stt_available() -> bool:
    """Return True when an offline model can be loaded."""

    return _load_vosk_model() is not None


def transcribe_audio_offline(audio: sr.AudioData) -> str | None:
    """Transcribe audio using Vosk when available."""

    model = _load_vosk_model()
    if model is None:
        return None

    try:
        from vosk import KaldiRecognizer

        recognizer = KaldiRecognizer(model, 16000)
        recognizer.AcceptWaveform(audio.get_raw_data(convert_rate=16000, convert_width=2))
        result = json.loads(recognizer.FinalResult())
        text = result.get("text", "").strip()
        return text or None
    except (ImportError, OSError, RuntimeError, ValueError, JSONDecodeError):
        return None


def transcribe_audio(
    recognizer: sr.Recognizer,
    audio: sr.AudioData,
    language: str = "en-US",
    prefer_offline: bool = False,
) -> str | None:
    """Try online speech recognition first, then offline fallback."""

    if prefer_offline and offline_stt_available():
        offline = transcribe_audio_offline(audio)
        if offline:
            return offline

    try:
        return recognizer.recognize_google(audio, language=language)
    except (sr.UnknownValueError, sr.RequestError):
        if offline_stt_available():
            return transcribe_audio_offline(audio)
        return None


def recognition_mode() -> str:
    """Expose the currently available recognition mode for health checks."""

    return "offline" if offline_stt_available() else "online"
