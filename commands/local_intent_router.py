"""Fast local command routing for common free-first assistant actions."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

ActionPayload = dict[str, Any]

APP_ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "steam": "steam",
    "epic": "epic",
    "epic games": "epic",
    "spotify": "spotify",
    "vscode": "vscode",
    "visual studio code": "vscode",
    "vs code": "vscode",
    "notepad": "notepad",
    "calculator": "calculator",
    "explorer": "explorer",
    "task manager": "taskmgr",
    "discord": "discord",
    "whatsapp": "whatsapp",
    "word": "word",
    "excel": "excel",
    "powerpoint": "powerpoint",
    "paint": "paint",
    "cmd": "cmd",
}
SORTED_APP_ALIASES = tuple(sorted(APP_ALIASES, key=len, reverse=True))

DIRECT_ACTION_PATTERNS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("current time", "what time", "time now"), "get_time"),
    (("current date", "what date", "what day", "today date"), "get_date"),
    (("battery", "battery status"), "get_battery"),
    (("ram", "memory usage", "memory status"), "get_ram"),
    (("cpu", "processor usage", "cpu usage"), "get_cpu"),
    (("screenshot", "screen shot", "take screenshot"), "screenshot"),
    (("read clipboard", "clipboard read"), "read_clipboard"),
    (("summarize clipboard", "clipboard summary"), "summarize_clipboard"),
    (("read notes", "list notes"), "read_notes"),
    (("memory stats", "memory status"), "memory_stats"),
    (("memory summary",), "memory_summary"),
    (("memory health",), "memory_health"),
    (("memory habits", "my habits", "command habits"), "memory_habits"),
    (("daily summary", "daily briefing"), "daily_summary"),
    (("clean memory", "prune memory", "cleanup memory"), "prune_memory"),
)

TRAILING_SEARCH_WORDS = (" search",)
WEBSITE_ALIASES = {
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "openai": "https://openai.com",
    "groq": "https://console.groq.com",
}
WINDOW_ACTIONS = {
    "minimize all windows": "minimize_all",
    "minimize all": "minimize_all",
    "show desktop": "minimize_all",
    "maximize window": "maximize_window",
    "maximize current window": "maximize_window",
    "close window": "close_window",
    "close current window": "close_window",
}
KEY_ACTIONS = {
    "mute volume": "volumemute",
    "unmute volume": "volumemute",
    "volume up": "volumeup",
    "turn volume up": "volumeup",
    "increase volume": "volumeup",
    "volume down": "volumedown",
    "turn volume down": "volumedown",
    "decrease volume": "volumedown",
}
SPOTIFY_ACTIONS = {
    "play music": "spotify_play",
    "resume music": "spotify_play",
    "pause music": "spotify_pause",
    "stop music": "spotify_pause",
    "next track": "spotify_next",
    "next song": "spotify_next",
    "previous track": "spotify_prev",
    "previous song": "spotify_prev",
    "what is playing on spotify": "spotify_current",
    "current spotify song": "spotify_current",
}


def normalize_command(command: str) -> str:
    """Return a lowercase ASCII command string suitable for matching."""

    lowered = (command or "").strip().lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    ascii_text = re.sub(r"['`]", " ", ascii_text)
    ascii_text = re.sub(r"[^a-z0-9:/?&.=+\- ]+", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def _payload(action: str, params: dict[str, Any] | None = None, response: str = "") -> ActionPayload:
    return {"action": action, "params": params or {}, "response": response}


def _match_direct_action(normalized: str) -> ActionPayload | None:
    for patterns, action in DIRECT_ACTION_PATTERNS:
        if any(pattern in normalized for pattern in patterns):
            return _payload(action)
    return None


def _match_open_app(normalized: str) -> ActionPayload | None:
    for alias in SORTED_APP_ALIASES:
        app = APP_ALIASES[alias]
        if normalized in {f"{alias} open", f"open {alias}", f"launch {alias}"}:
            return _payload("open_app", {"app": app}, f"Opening {app}, sir.")
    return None


def _normalize_url(value: str) -> str:
    value = value.strip()
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"


def _match_open_web(normalized: str) -> ActionPayload | None:
    prefixes = ("open ", "go to ")
    for prefix in prefixes:
        if not normalized.startswith(prefix):
            continue
        target = normalized[len(prefix) :].strip()
        if target in WEBSITE_ALIASES:
            return _payload("open_web", {"url": WEBSITE_ALIASES[target]}, f"Opening {target}, sir.")
        if "." in target and " " not in target:
            return _payload("open_web", {"url": _normalize_url(target)}, f"Opening {target}, sir.")
    return None


def _strip_trailing_search_word(query: str) -> str:
    for suffix in TRAILING_SEARCH_WORDS:
        if query.endswith(suffix):
            return query[: -len(suffix)].strip()
    return query.strip()


def _match_google_search(normalized: str) -> ActionPayload | None:
    prefixes = ("google ", "search google for ", "google search ", "search for ", "look up ", "find ")
    for prefix in prefixes:
        if normalized.startswith(prefix):
            query = _strip_trailing_search_word(normalized[len(prefix) :])
            if query:
                return _payload("search_google", {"query": query}, f"Searching Google for {query}, sir.")
    return None


def _match_control_action(normalized: str) -> ActionPayload | None:
    if normalized in WINDOW_ACTIONS:
        return _payload(WINDOW_ACTIONS[normalized])
    if normalized in KEY_ACTIONS:
        return _payload("press_key", {"key": KEY_ACTIONS[normalized]})
    return None


def _match_spotify_action(normalized: str) -> ActionPayload | None:
    if normalized in SPOTIFY_ACTIONS:
        return _payload(SPOTIFY_ACTIONS[normalized])
    if normalized.startswith("play ") and normalized.endswith(" on spotify"):
        query = normalized.removeprefix("play ").removesuffix(" on spotify").strip()
        if query:
            return _payload("spotify_search", {"query": query}, f"Playing {query} on Spotify, sir.")
    return None


def _match_note_write(normalized: str) -> ActionPayload | None:
    prefixes = ("remember ", "add note ", "note ")
    for prefix in prefixes:
        if normalized.startswith(prefix):
            text = normalized[len(prefix) :].strip()
            if text:
                return _payload("add_note", {"text": text})
    return None


def route_local_intent(command: str) -> ActionPayload | None:
    """Return an action payload for common commands that do not need an LLM."""

    normalized = normalize_command(command)
    if not normalized:
        return None

    for matcher in (
        _match_note_write,
        _match_open_app,
        _match_open_web,
        _match_google_search,
        _match_control_action,
        _match_spotify_action,
        _match_direct_action,
    ):
        action = matcher(normalized)
        if action is not None:
            return action
    return None


__all__ = ["normalize_command", "route_local_intent"]
