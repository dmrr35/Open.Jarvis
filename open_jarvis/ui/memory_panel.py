"""User-visible memory management helpers."""

from __future__ import annotations

import copy
from typing import Any

from open_jarvis.memory.privacy_mode import build_privacy_session, mask_sensitive_value


def build_memory_panel(memory: dict[str, Any], *, privacy_enabled: bool = False) -> dict[str, Any]:
    """Return a safe snapshot suitable for a memory settings panel."""

    snapshot = copy.deepcopy(memory)
    preferences = mask_sensitive_value(snapshot.get("preferences", {}))
    notes = snapshot.get("notes", [])
    habits = snapshot.get("habits", {})
    return {
        "preferences": preferences,
        "notes": notes,
        "recent_notes": notes[-5:],
        "habits": habits,
        "privacy": build_privacy_session(enabled=privacy_enabled),
        "counts": {
            "preferences": len(preferences),
            "notes": len(notes),
            "habits": len(habits),
        },
    }


def update_preference(memory: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
    """Update a preference without mutating the caller's memory object."""

    updated = copy.deepcopy(memory)
    updated.setdefault("preferences", {})[key] = value
    return updated


def delete_note(memory: dict[str, Any], index: int) -> dict[str, Any]:
    """Delete a note by index when it exists."""

    updated = copy.deepcopy(memory)
    notes = list(updated.get("notes", []))
    if 0 <= index < len(notes):
        del notes[index]
    updated["notes"] = notes
    return updated
