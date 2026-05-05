"""Voice personality helpers for JARVIS."""

from __future__ import annotations

import datetime
import random

JOKES = [
    "By the way, sir - why do programmers prefer dark mode? Because light attracts bugs.",
    "On a side note, sir - I tried to come up with a joke about infinity, but I just couldn't find an end to it.",
    "Incidentally, sir - there are 10 types of people in this world. Those who understand binary, and those who don't.",
    "A random thought, sir - why do Java developers wear glasses? Because they don't C sharp.",
    "Speaking of which, sir - a SQL query walks into a bar, walks up to two tables and asks: can I join you?",
    "Fun fact, sir - the first computer bug was an actual bug. A moth, to be precise, found in a Harvard computer in 1947.",
    "Did you know, sir - the average person spends 6 months of their lifetime waiting for red lights to turn green?",
    "By the way, sir - I once told a joke about UDP. I don't know if you got it.",
    "On another note, sir - why was the computer cold? It left its Windows open.",
    "Just a thought, sir - I would tell you a joke about construction, but I'm still working on it.",
]

GOODBYES = [
    "It's been a pleasure serving you today, sir. Jarvis signing off.",
    "Until next time, sir. I'll keep the systems warm for your return.",
    "Farewell, sir. The lab is yours. I'll be right here when you need me.",
    "Signing off now, sir. Don't forget - I'm always just a word away.",
    "Goodbye, sir. It was an honour, as always. Jarvis shutting down.",
    "Take care, sir. I'll have everything ready for when you're back.",
]


def safe_speak(text: str, *, speak, send_log=None, logger=None) -> bool:
    """Speak without letting a TTS failure stop the assistant runtime."""

    try:
        speak(text)
    except (RuntimeError, OSError, ValueError) as exc:
        if logger is not None:
            logger.warning("Voice output failed: %s", exc)
        if send_log is not None:
            send_log(f"[ERROR] Voice output failed: {exc}")
        return False
    return True


def greet(*, speak, send_log, logger=None) -> None:
    """Speak the initial greeting and push it to the UI log."""

    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    elif 18 <= hour < 22:
        greeting = "Good evening"
    else:
        greeting = "Good night"
    safe_speak(f"{greeting}, sir. Jarvis is online. Say Jarvis to activate me.", speak=speak, send_log=send_log, logger=logger)
    send_log(f"JARVIS: {greeting}, sir. All systems are ready.")


def say_goodbye(*, speak, send_log=None, logger=None) -> None:
    """Speak a personalised goodbye."""

    hour = datetime.datetime.now().hour
    if 22 <= hour or hour < 6:
        safe_speak(random.choice(GOODBYES) + " Get some rest, sir.", speak=speak, send_log=send_log, logger=logger)
    else:
        safe_speak(random.choice(GOODBYES), speak=speak, send_log=send_log, logger=logger)


def maybe_tell_joke(*, speak, send_log, logger, state: dict) -> None:
    """Randomly tell a joke after a few commands."""

    state["command_count"] = state.get("command_count", 0) + 1
    if state["command_count"] >= state.get("joke_interval", 5):
        state["command_count"] = 0
        state["joke_interval"] = random.randint(5, 8)
        joke = random.choice(JOKES)
        logger.info("Telling random joke.")
        if safe_speak(joke, speak=speak, send_log=send_log, logger=logger):
            send_log(f"JARVIS: {joke}")
