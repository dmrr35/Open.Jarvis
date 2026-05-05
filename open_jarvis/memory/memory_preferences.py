"""Preference detection and storage helpers."""

from __future__ import annotations

import re

from open_jarvis.memory.memory_store import load_memory, save_memory


def set_preference(key: str, value):
    """Save a user preference."""

    memory = load_memory()
    if key in memory["preferences"]:
        memory["preferences"][key] = value
    else:
        memory["preferences"]["custom"][key] = value
    save_memory(memory)


def get_preference(key: str):
    """Get a user preference."""

    memory = load_memory()
    if key in memory["preferences"]:
        return memory["preferences"][key]
    return memory["preferences"]["custom"].get(key)


def detect_and_save_preference(command: str):
    """Detect and save preferences from natural language."""

    command = command.lower()

    if "always play" in command or "favorite music" in command or "favorite artist" in command:
        for trigger in ["always play", "favorite music is", "favorite artist is"]:
            if trigger in command:
                artist = command.split(trigger)[-1].strip()
                if artist:
                    set_preference("favorite_music", artist)
                    return f"Got it, sir. I'll remember that you love {artist}."

    if "default volume" in command or "always volume" in command or "set volume to" in command:
        numbers = re.findall(r"\d+", command)
        if numbers:
            volume = int(numbers[0])
            set_preference("preferred_volume", volume)
            return f"Noted, sir. Default volume set to {volume} percent."

    if "always open" in command or "favorite app" in command:
        apps = ["chrome", "spotify", "steam", "epic", "vscode", "discord"]
        for app in apps:
            if app in command:
                set_preference("favorite_app", app)
                return f"Understood, sir. I'll remember you prefer {app}."

    return None
