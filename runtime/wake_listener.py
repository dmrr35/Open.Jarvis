"""Wake-word listener helpers."""

from __future__ import annotations

import os

import speech_recognition as sr

from observability import record_runtime_event
from speech_backend import recognition_mode, transcribe_audio

WAKE_WORD = os.getenv("JARVIS_WAKE_WORD", "jarvis").strip().lower() or "jarvis"
ACTIVE_TIMEOUT = int(os.getenv("JARVIS_ACTIVE_TIMEOUT", "60"))

_wake_recognizer = sr.Recognizer()
_wake_recognizer.energy_threshold = int(os.getenv("JARVIS_ENERGY_THRESHOLD", "300"))
_wake_recognizer.dynamic_energy_threshold = True

active = False


def listen_for_wake_word(*, logger, send_log) -> None:
    """Listen for the wake word in the background."""

    global active
    while True:
        try:
            with sr.Microphone() as source:
                _wake_recognizer.adjust_for_ambient_noise(source, duration=0.1)
                audio = _wake_recognizer.listen(source, timeout=3, phrase_time_limit=3)
            text = transcribe_audio(_wake_recognizer, audio, language="en-US", prefer_offline=True)
            if not text:
                continue
            text = text.lower()
            if WAKE_WORD in text:
                active = True
                print("\n🟢 Wake word detected!")
                send_log("WAKE WORD DETECTED")
                record_runtime_event("wake_word", "Wake word detected", "info", {"mode": recognition_mode()})
        except (OSError, RuntimeError, ValueError, sr.WaitTimeoutError):
            logger.debug("Wake-word listener swallowed an exception.", exc_info=True)
