"""Note storage helpers."""

from __future__ import annotations

import datetime

from memory_store import load_memory, save_memory


def add_note(note: str):
    """Save a note."""

    memory = load_memory()
    memory["notes"].append(
        {
            "text": note,
            "created_at": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
    )
    save_memory(memory)


def get_notes() -> list:
    """Return all saved notes."""

    memory = load_memory()
    return memory.get("notes", [])


def clear_notes():
    """Clear all notes."""

    memory = load_memory()
    memory["notes"] = []
    save_memory(memory)
