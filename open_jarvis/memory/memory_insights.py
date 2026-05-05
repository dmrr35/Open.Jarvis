"""Read-only helpers for memory analytics and prompt context."""

from __future__ import annotations

from collections.abc import Iterable

MAX_NOTES = 25
MAX_HABITS = 50


def get_memory_quality_score(memory: dict | None = None) -> int:
    """Return a simple 0-100 memory quality score."""

    memory = memory or {}
    score = 0

    prefs = memory.get("preferences", {})
    if prefs.get("favorite_music"):
        score += 15
    if prefs.get("favorite_app"):
        score += 15
    if prefs.get("preferred_volume") is not None:
        score += 10
    if memory.get("notes"):
        score += min(20, len(memory.get("notes", [])) * 5)

    habits = memory.get("habits", {})
    if habits:
        score += min(25, len(habits) * 10)

    total_commands = memory.get("total_commands", 0)
    score += min(15, total_commands // 2)

    return min(100, score)


def build_memory_health_report(memory: dict | None = None) -> dict:
    """Return a lightweight memory health report with a recommendation."""

    memory = memory or {}
    score = get_memory_quality_score(memory)
    issues = []

    if not memory.get("preferences", {}).get("favorite_music"):
        issues.append("No favorite music preference saved yet.")
    if not memory.get("preferences", {}).get("favorite_app"):
        issues.append("No favorite app preference saved yet.")
    if len(memory.get("notes", [])) > MAX_NOTES:
        issues.append("Notes are getting long and should be pruned.")
    if len(memory.get("habits", {})) > MAX_HABITS:
        issues.append("Habit list is growing and should be compacted.")

    if score >= 80:
        recommendation = "Memory health is strong. Keep using Jarvis and it will keep adapting."
    elif score >= 50:
        recommendation = "Memory is useful, but pruning and a few more preferences will improve it."
    else:
        recommendation = "Pruning and preference training would help Jarvis learn faster."

    if issues:
        recommendation = recommendation + " Pruning is recommended."

    return {"score": score, "issues": issues, "recommendation": recommendation}


def summarize_recent_activity(
    limit: int = 5,
    *,
    memory: dict | None = None,
    top_habits: Iterable[tuple[str, int]] | None = None,
) -> str:
    """Summarize recent commands and notes for docs or prompts."""

    memory = memory or {}
    recent_notes = memory.get("notes", [])[-limit:]
    habits = list(top_habits or [])
    parts = []

    if habits:
        parts.append("Top habits: " + ", ".join(f"{cmd} ({count})" for cmd, count in habits[:limit]))
    if recent_notes:
        parts.append("Recent notes: " + "; ".join(note["text"] for note in recent_notes))
    if not parts:
        return "No recent memory activity yet."
    return " | ".join(parts)


def build_context_prompt(
    *,
    memory: dict | None = None,
    recent: list[dict] | None = None,
    top_habits: list[tuple[str, int]] | None = None,
) -> str:
    """Build a context string to include in Groq prompts."""

    memory = memory or {}
    prefs = memory.get("preferences", {})
    recent = recent or []
    top_habits = top_habits or []

    parts = []

    if prefs.get("favorite_music"):
        parts.append(f"User's favorite music: {prefs['favorite_music']}")
    if prefs.get("favorite_app"):
        parts.append(f"User's most used app: {prefs['favorite_app']}")
    if prefs.get("preferred_volume"):
        parts.append(f"User's preferred volume: {prefs['preferred_volume']}%")
    if top_habits:
        habit_str = ", ".join([f'"{h[0]}"' for h in top_habits])
        parts.append(f"Most used commands: {habit_str}")
    if recent:
        recent_str = " | ".join([f"{r['role']}: {r['content']}" for r in recent])
        parts.append(f"Recent conversation: {recent_str}")

    if not parts:
        return ""
    return "USER CONTEXT (use this to personalize responses):\n" + "\n".join(parts)
