"""Compatibility re-exports for split memory state modules."""

from __future__ import annotations

from memory_habits import get_top_habits, track_command
from memory_notes import add_note, clear_notes, get_notes
from memory_preferences import detect_and_save_preference, get_preference, set_preference
from memory_short_term import add_to_short_term, clear_short_term, get_short_term, get_short_term_for_groq

__all__ = [
    "add_note",
    "add_to_short_term",
    "clear_notes",
    "clear_short_term",
    "detect_and_save_preference",
    "get_notes",
    "get_preference",
    "get_short_term",
    "get_short_term_for_groq",
    "get_top_habits",
    "set_preference",
    "track_command",
]
