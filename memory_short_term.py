"""Short-term conversation memory."""

from __future__ import annotations

import datetime

_short_term = []
MAX_SHORT_TERM = 10


def add_to_short_term(role: str, content: str):
    """Add a message to short-term memory."""

    global _short_term
    _short_term.append(
        {
            "role": role,
            "content": content,
            "time": datetime.datetime.now().strftime("%H:%M"),
        }
    )
    if len(_short_term) > MAX_SHORT_TERM:
        _short_term = _short_term[-MAX_SHORT_TERM:]


def get_short_term() -> list:
    """Return recent conversation history."""

    return _short_term.copy()


def get_short_term_for_groq() -> list:
    """Return short-term memory formatted for Groq API messages."""

    messages = []
    for item in _short_term:
        role = "user" if item["role"] == "user" else "assistant"
        messages.append({"role": role, "content": item["content"]})
    return messages


def clear_short_term():
    """Clear short-term memory."""

    global _short_term
    _short_term = []
