"""Backward-compatible wake-word helpers."""

from __future__ import annotations

from open_jarvis.runtime.command_listener import listen_for_command
from open_jarvis.runtime.wake_listener import ACTIVE_TIMEOUT, WAKE_WORD, listen_for_wake_word

__all__ = ["WAKE_WORD", "ACTIVE_TIMEOUT", "listen_for_wake_word", "listen_for_command"]
