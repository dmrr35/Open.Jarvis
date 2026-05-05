"""Memory-related actions."""

from __future__ import annotations

from memory import (
    add_note,
    build_memory_health_report,
    get_notes,
    get_stats,
    get_top_habits,
    prune_memory,
    summarize_recent_activity,
)


def handle_memory_action(action: str, params: dict, context: dict) -> bool | None:
    """Handle memory and note actions."""

    speak = context["speak"]
    logger = context["logger"]

    if action == "memory_stats":
        stats = get_stats()
        speak(
            f"You have given me {stats['total_commands']} commands so far, sir. "
            f"I have {stats['notes_count']} notes saved and I know {stats['habits_count']} of your habits."
        )
        return True

    if action == "memory_habits":
        habits = get_top_habits(5)
        if habits:
            habit_list = ", ".join([f"{habit[0]} ({habit[1]} times)" for habit in habits])
            speak(f"Your most used commands are: {habit_list}, sir.")
        else:
            speak("I haven't learned your habits yet, sir. Keep using me and I'll figure it out.")
        return True

    if action == "memory_health":
        report = build_memory_health_report()
        speak(f"Memory health is {report['score']} out of 100, sir. {report['recommendation']}")
        return True

    if action == "memory_summary":
        speak(summarize_recent_activity())
        return True

    if action == "daily_summary":
        stats = get_stats()
        activity = summarize_recent_activity()
        speak(
            "Daily summary, sir. "
            f"You have issued {stats['total_commands']} commands. "
            f"I have {stats['notes_count']} notes saved and {stats['habits_count']} habit patterns. "
            f"{activity}"
        )
        return True

    if action == "prune_memory":
        pruned = prune_memory()
        speak("Memory has been pruned, sir. I kept the most recent notes and habits.")
        logger.info("Memory pruned: notes=%s habits=%s", len(pruned.get("notes", [])), len(pruned.get("habits", {})))
        return True

    if action == "add_note":
        if context.get("privacy_mode"):
            speak("Privacy mode is active, sir. I did not save that note to memory.")
            return True
        text = params.get("text", "")
        if text:
            add_note(text)
            speak(f"Note saved, sir: {text}")
        else:
            speak("What would you like me to note, sir?")
        return True

    if action == "read_notes":
        notes = get_notes()
        if notes:
            speak(f"You have {len(notes)} notes, sir.")
            for index, note in enumerate(notes[-5:], 1):
                speak(f"Note {index}: {note['text']}")
        else:
            speak("You have no saved notes, sir.")
        return True

    return None
