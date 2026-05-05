"""Context-aware command suggestions."""

from __future__ import annotations


def suggest_commands(context: dict) -> list[dict[str, str]]:
    """Suggest discoverable commands without proposing blocked destructive actions."""

    suggestions: list[dict[str, str]] = []
    missing = set(context.get("missing", []))
    if "spotify" in missing:
        suggestions.append({"command": "finish spotify setup", "category": "setup", "why": "Music commands need Spotify credentials."})
    if context.get("last_action") == "music":
        suggestions.append({"command": "play my favorite music", "category": "music", "why": "Your last interaction was music-focused."})
    suggestions.append({"command": "run health check", "category": "maintenance", "why": "Catch configuration issues early."})
    if context.get("permission_profile") != "safe":
        suggestions.append({"command": "lock the computer", "category": "runtime", "why": "Secure the current session quickly."})
    return suggestions
