"""Typed voice UX errors for optional audio flows."""

from __future__ import annotations


class VoiceRuntimeError(RuntimeError):
    """Base class for recoverable voice runtime failures."""

    code = "voice_runtime_error"

    def as_diagnostic(self) -> dict[str, str]:
        return {"code": self.code, "message": str(self)}


class MicrophoneUnavailableError(VoiceRuntimeError):
    """Raised when a microphone-dependent action cannot continue."""

    code = "microphone_unavailable"


class SpeechRecognitionUnavailableError(VoiceRuntimeError):
    """Raised when STT is unavailable or fails."""

    code = "speech_recognition_unavailable"


class WakeWordDisabled(VoiceRuntimeError):
    """Raised when wake-word flow is disabled by configuration."""

    code = "wake_word_disabled"


class TTSUnavailableError(VoiceRuntimeError):
    """Raised when speech output is unavailable."""

    code = "tts_unavailable"
