"""Groq-backed command analysis and summarization helpers."""

from __future__ import annotations

import json
import os
import time

from dotenv import load_dotenv
from groq import Groq, GroqError

from jarvis_admin import format_actionable_message
from jarvis_logging import get_logger
from memory import build_context_prompt
from observability import record_runtime_event

load_dotenv()

logger = get_logger("commands")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_COOLDOWN_SECONDS = 120
_groq_cooldown_until = 0.0


def _env_flag_enabled(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def groq_enabled() -> bool:
    """Return whether optional Groq routing is enabled by configuration."""

    return _env_flag_enabled("JARVIS_ENABLE_GROQ", default=True)


client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY and groq_enabled() else None

if client is None:
    logger.warning("Groq API key not found. Running in local-only mode.")

SYSTEM_PROMPT = """
You are JARVIS, Tony Stark's personal AI assistant from Iron Man.
You are highly intelligent, witty, and always professional.
You speak in a formal British manner and address the user as "sir".
You remember the user's preferences and adapt to their habits.
You are proactive — if you notice patterns, mention them.
You occasionally make subtle, dry humor remarks.
Always be concise but complete in your responses.
You are JARVIS, an AI assistant like in Iron Man.
Think carefully before responding. Always return valid JSON.
Analyze the user's command and return ONLY valid JSON.

IMPORTANT: If the command contains multiple tasks (e.g. "open chrome and go to youtube"),
return a list of actions. Otherwise return a single action object.

Single action format:
{"action": "ACTION_NAME", "params": {}, "response": "What JARVIS says"}

Multiple actions format:
{"actions": [{"action": "ACTION_NAME", "params": {}}, {"action": "ACTION_NAME", "params": {}}], "response": "What JARVIS says"}

Available actions:
- "open_app": {"app": "chrome|steam|epic|spotify|vscode|notepad|calculator|explorer|taskmgr|discord|whatsapp|word|excel|powerpoint|paint|cmd"}
- "open_web": {"url": "full URL"}
- "search_google": {"query": "search term"}
- "get_time": {}
- "get_date": {}
- "get_battery": {}
- "get_ram": {}
- "get_cpu": {}
- "screenshot": {}
- "read_clipboard": {}
- "summarize_clipboard": {}
- "type_text": {"text": "text to type"}
- "press_key": {"key": "enter|esc|space|tab|ctrl+c|ctrl+v|ctrl+z|ctrl+s|alt+f4|win|f5|delete|volumeup|volumedown|volumemute"}
- "mouse_click": {"x": 0, "y": 0, "button": "left|right|double"}
- "scroll": {"direction": "up|down", "amount": 3}
- "minimize_all": {}
- "maximize_window": {}
- "close_window": {}
- "lock_screen": {}
- "shutdown": {}
- "restart": {}
- "sleep": {}
- "spotify_play": {}
- "spotify_pause": {}
- "spotify_next": {}
- "spotify_prev": {}
- "spotify_volume": {"level": 50}
- "spotify_search": {"query": "song or artist name"}
- "spotify_current": {}
- "memory_stats": {}
- "memory_habits": {}
- "memory_health": {}
- "memory_summary": {}
- "prune_memory": {}
- "add_note": {"text": "note text"}
- "read_notes": {}
- "talk": {}
"""


def _resolve_client(provided_client):
    return provided_client if provided_client is not None else client


def get_groq_model() -> str:
    """Return the configured free-first Groq routing model."""

    return os.getenv("JARVIS_GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL


def is_groq_cooling_down(now: float | None = None) -> bool:
    """Return True when Groq should be skipped after a recent rate-limit error."""

    return (time.time() if now is None else now) < _groq_cooldown_until


def activate_groq_cooldown(seconds: int = GROQ_COOLDOWN_SECONDS, now: float | None = None) -> None:
    """Temporarily avoid Groq after free-tier/rate-limit failures."""

    global _groq_cooldown_until
    _groq_cooldown_until = (time.time() if now is None else now) + max(1, seconds)


def _rate_limit_fallback() -> dict:
    return {
        "action": "talk",
        "params": {},
        "response": format_actionable_message(
            "I reached the free Groq quota for the moment, sir.",
            "Cloud AI routing is cooling down to avoid repeatedly hitting the free-tier limit.",
            "I will keep handling simple commands locally and try cloud routing again shortly.",
        ),
    }


def extract_action_json(text: str) -> dict:
    """Extract the first JSON object from a model response."""

    value = (text or "").strip()
    if "```" in value:
        chunks = value.split("```")
        value = next((chunk[4:].strip() if chunk.startswith("json") else chunk.strip() for chunk in chunks if "{" in chunk), value)

    start = value.find("{")
    end = value.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in Groq response")
    return json.loads(value[start : end + 1])


def analyze_with_groq(command, *, client=None, logger=logger):
    """Send a command to Groq with memory context and return action JSON."""

    active_client = _resolve_client(client)
    if is_groq_cooling_down():
        logger.warning("Groq analysis skipped because cooldown is active.")
        record_runtime_event("groq_cooldown", "Groq analysis skipped during cooldown", "warning")
        return _rate_limit_fallback()

    if active_client is None:
        logger.warning("Groq API key not found. Running in local-only mode.")
        record_runtime_event("groq_missing", "Groq analysis skipped", "warning")
        return {
            "action": "talk",
            "params": {},
            "response": format_actionable_message(
                "Groq API key not found. Running in local-only mode.",
                "AI command routing is disabled because Groq is not configured or not enabled.",
                "Add GROQ_API_KEY to your .env file and set JARVIS_ENABLE_GROQ=true to enable cloud routing.",
            ),
        }

    try:
        logger.info("Analyzing command with Groq: %s", command)
        record_runtime_event("groq_request", "Analyzing command with Groq", "info", {"command": command[:120]})
        context = build_context_prompt()
        system = f"{context}\n\n{SYSTEM_PROMPT}" if context else SYSTEM_PROMPT
        response = active_client.chat.completions.create(
            model=get_groq_model(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": command},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return extract_action_json(response.choices[0].message.content)
    except (GroqError, json.JSONDecodeError, ValueError, AttributeError) as exc:
        logger.warning("Groq error while analyzing command: %s", exc)
        record_runtime_event("groq_error", "Groq analysis failed", "warning", {"error": str(exc)})
        if "rate" in str(exc).lower() or "quota" in str(exc).lower() or "429" in str(exc):
            activate_groq_cooldown()
            return _rate_limit_fallback()
        return {
            "action": "talk",
            "params": {},
            "response": format_actionable_message(
                "I encountered an error, sir.",
                "Groq returned an invalid response or the request failed.",
                "Check GROQ_API_KEY, internet access, and try again.",
            ),
        }


def summarize_text(text, *, client=None, logger=logger):
    """Summarize text using Groq."""

    active_client = _resolve_client(client)
    if active_client is None:
        logger.warning("Summarization skipped because GROQ_API_KEY is missing.")
        return None

    try:
        if len(text) > 4000:
            text = text[:4000]
        response = active_client.chat.completions.create(
            model=get_groq_model(),
            messages=[{"role": "user", "content": f"Summarize this in 3-4 sentences as JARVIS would:\n\n{text}"}],
            temperature=0.1,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except (GroqError, AttributeError) as exc:
        logger.warning("Groq summarization failed: %s", exc)
        record_runtime_event("summarization_error", "Groq summarization failed", "warning", {"error": str(exc)})
        return None


__all__ = [
    "SYSTEM_PROMPT",
    "activate_groq_cooldown",
    "analyze_with_groq",
    "client",
    "extract_action_json",
    "get_groq_model",
    "is_groq_cooling_down",
    "summarize_text",
]
