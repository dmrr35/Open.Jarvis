"""Timer helpers used by the main runtime loop."""

from __future__ import annotations

import threading
import time


def parse_duration(command: str) -> int:
    """Extract a duration in seconds from a natural language command."""

    import re

    seconds = 0
    m = re.search(r"(\d+)\s*(hour|saat)", command)
    if m:
        seconds += int(m.group(1)) * 3600
    m = re.search(r"(\d+)\s*(minute|min|dakika)", command)
    if m:
        seconds += int(m.group(1)) * 60
    m = re.search(r"(\d+)\s*(second|sec|saniye)", command)
    if m:
        seconds += int(m.group(1))
    return seconds


def start_timer(seconds: int, message: str = "Time is up, sir.", *, speak, send_log, logger) -> None:
    """Start a countdown in the background."""

    def countdown():
        time.sleep(seconds)
        speak(message)
        send_log(f"JARVIS: {message}")

    threading.Thread(target=countdown, daemon=True).start()
    logger.info("Timer started for %s seconds.", seconds)
    print(f"⏱️  Timer started: {seconds} seconds")


def handle_timer_command(command: str, *, speak, send_log, logger) -> bool:
    """Check and handle timer commands."""

    if any(k in command for k in ["timer", "alarm", "remind me in", "set a timer", "countdown"]):
        seconds = parse_duration(command)
        if seconds > 0:
            minutes = seconds // 60
            remaining = seconds % 60
            if minutes > 0 and remaining > 0:
                duration_str = f"{minutes} minutes and {remaining} seconds"
            elif minutes > 0:
                duration_str = f"{minutes} minute{'s' if minutes > 1 else ''}"
            else:
                duration_str = f"{seconds} seconds"
            speak(f"Timer set for {duration_str}, sir. I will notify you when it's done.")
            start_timer(seconds, f"Sir, your {duration_str} timer is up.", speak=speak, send_log=send_log, logger=logger)
            return True
        speak("I couldn't understand the duration, sir. Please say something like: set a timer for 10 minutes.")
        return True
    return False
