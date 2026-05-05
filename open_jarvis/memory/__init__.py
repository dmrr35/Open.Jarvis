"""Compatibility layer for memory helpers."""

from __future__ import annotations

from open_jarvis.memory.memory_habits import get_top_habits, track_command
from open_jarvis.memory.memory_insights import (
    build_context_prompt as build_context_prompt_insights,
)
from open_jarvis.memory.memory_insights import (
    build_memory_health_report as build_memory_health_report_insights,
)
from open_jarvis.memory.memory_insights import (
    get_memory_quality_score as get_memory_quality_score_insights,
)
from open_jarvis.memory.memory_insights import (
    summarize_recent_activity as summarize_recent_activity_insights,
)
from open_jarvis.memory.memory_notes import add_note, clear_notes, get_notes
from open_jarvis.memory.memory_preferences import detect_and_save_preference, get_preference, set_preference
from open_jarvis.memory.memory_short_term import add_to_short_term, clear_short_term, get_short_term, get_short_term_for_groq
from open_jarvis.memory.memory_store import DEFAULT_MEMORY, MAX_HABITS, MAX_NOTES, load_memory, prune_memory, save_memory


def build_context_prompt() -> str:
    memory = load_memory()
    return build_context_prompt_insights(
        memory=memory,
        recent=get_short_term()[-3:] if get_short_term() else [],
        top_habits=get_top_habits(3),
    )


def get_stats() -> dict:
    memory = load_memory()
    quality = get_memory_quality_score_insights(memory)
    return {
        "total_commands": memory.get("total_commands", 0),
        "notes_count": len(memory.get("notes", [])),
        "habits_count": len(memory.get("habits", {})),
        "created_at": memory.get("created_at", "Unknown"),
        "last_seen": memory.get("last_seen", "Unknown"),
        "short_term_count": len(get_short_term()),
        "quality_score": quality,
    }


def get_memory_quality_score(memory: dict | None = None) -> int:
    return get_memory_quality_score_insights(load_memory() if memory is None else memory)


def build_memory_health_report(memory: dict | None = None) -> dict:
    return build_memory_health_report_insights(load_memory() if memory is None else memory)


def summarize_recent_activity(limit: int = 5) -> str:
    return summarize_recent_activity_insights(
        limit=limit,
        memory=load_memory(),
        top_habits=get_top_habits(limit),
    )


_memory = load_memory()


__all__ = [
    "DEFAULT_MEMORY",
    "MAX_HABITS",
    "MAX_NOTES",
    "add_note",
    "add_to_short_term",
    "build_context_prompt",
    "build_memory_health_report",
    "clear_notes",
    "clear_short_term",
    "detect_and_save_preference",
    "get_notes",
    "get_preference",
    "get_short_term",
    "get_short_term_for_groq",
    "get_memory_quality_score",
    "get_stats",
    "get_top_habits",
    "load_memory",
    "prune_memory",
    "save_memory",
    "set_preference",
    "summarize_recent_activity",
    "track_command",
]
