"""Runtime and desktop actions."""

from __future__ import annotations

import datetime
import os
import time
import webbrowser

import psutil
import pyautogui
import pyperclip

from jarvis_admin import format_actionable_message
from observability import record_runtime_event
from process_runner import launch_process, run_command
from runtime_safety import block_message, is_destructive_action, is_destructive_action_allowed
from url_safety import build_google_search_url, normalize_web_url

APPLICATIONS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "steam": [
        r"C:\Program Files (x86)\Steam\steam.exe",
        r"C:\Program Files\Steam\steam.exe",
    ],
    "epic": [
        r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
    ],
    "spotify": [
        os.path.join(os.environ.get("APPDATA", ""), r"Spotify\Spotify.exe"),
    ],
    "discord": [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Discord\Update.exe"),
        os.path.join(os.environ.get("APPDATA", ""), r"Discord\Discord.exe"),
    ],
    "vscode": [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "word": [r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"],
    "excel": [r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"],
    "powerpoint": [r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"],
    "paint": ["mspaint.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "explorer": ["explorer.exe"],
    "taskmgr": ["taskmgr.exe"],
    "cmd": ["cmd.exe"],
    "whatsapp": [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"WhatsApp\WhatsApp.exe"),
    ],
}

DEFAULT_CPU_SAMPLE_INTERVAL = 0.1
LOCAL_SUMMARY_SENTENCE_LIMIT = 2


def env_float(name: str, default: float, minimum: float = 0.0) -> float:
    """Read a bounded float from the environment."""

    try:
        return max(minimum, float(os.getenv(name, default)))
    except ValueError:
        return default


def cpu_sample_interval() -> float:
    """Return a fast, configurable CPU sampling interval."""

    return env_float("JARVIS_CPU_SAMPLE_INTERVAL", DEFAULT_CPU_SAMPLE_INTERVAL)


def app_launch_delay() -> float:
    """Return a short post-launch pause for apps that need startup time."""

    return env_float("JARVIS_APP_LAUNCH_DELAY", 0.2)


def desktop_action_delay(name: str, default: float) -> float:
    """Return a configurable delay for desktop actions."""

    return env_float(name, default)


def summarize_text_locally(text: str, sentence_limit: int = LOCAL_SUMMARY_SENTENCE_LIMIT) -> str | None:
    """Return a small extractive summary without a cloud provider."""

    clean_text = " ".join((text or "").split())
    if not clean_text:
        return None
    sentences = [part.strip() for part in clean_text.replace("?", ".").replace("!", ".").split(".") if part.strip()]
    if not sentences:
        return clean_text[:400]
    summary = ". ".join(sentences[: max(1, sentence_limit)])
    return summary + ("." if not summary.endswith(".") else "")


def launch_app(app_name: str, *, speak, logger) -> bool:
    """Find and launch an application."""

    paths = APPLICATIONS.get(app_name.lower(), [app_name])
    for path in paths:
        if os.path.exists(path):
            launch_process([path])
            record_runtime_event("app_launch", f"launched {app_name}", "info", {"path": path})
            return True
    try:
        launch_process([app_name])
        record_runtime_event("app_launch", f"launched {app_name}", "info", {"path": app_name})
        return True
    except OSError as exc:
        logger.exception("Failed to launch app %s: %s", app_name, exc)
        record_runtime_event("app_launch_error", f"failed {app_name}", "warning", {"error": str(exc)})
        speak(
            format_actionable_message(
                f"I couldn't locate {app_name}, sir.",
                "The executable path was not found or Windows blocked the launch.",
                "Install the app, or provide the full executable path in APPLICATIONS.",
            )
        )
        return False


def handle_runtime_action(action: str, params: dict, context: dict) -> bool | None:
    """Handle desktop and system actions."""

    speak = context["speak"]
    logger = context["logger"]
    summarize_text = context.get("summarize_text")

    if is_destructive_action(action) and not is_destructive_action_allowed():
        logger.warning("Blocked destructive runtime action: %s", action)
        record_runtime_event("runtime_action_blocked", f"blocked {action}", "warning", {"action": action})
        speak(block_message(action))
        return False

    if action == "open_app":
        launch_app(params.get("app", ""), speak=speak, logger=logger)
        delay = app_launch_delay()
        if delay:
            time.sleep(delay)
        return True

    if action == "open_web":
        url = normalize_web_url(params.get("url", ""))
        if not url:
            speak("I blocked that URL, sir. Reason: only http and https browser links are allowed.")
            record_runtime_event("url_blocked", "blocked unsafe URL", "warning", {"action": action})
            return False
        webbrowser.open(url)
        return True

    if action == "search_google":
        webbrowser.open(build_google_search_url(params.get("query", "")))
        return True

    if action == "get_time":
        now = datetime.datetime.now().strftime("%H:%M")
        speak(f"The current time is {now}, sir.")
        return True

    if action == "get_date":
        today = datetime.datetime.now()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        speak(f"Today is {days[today.weekday()]}, {months[today.month - 1]} {today.day}, {today.year}.")
        return True

    if action == "get_battery":
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "on battery"
            speak(f"Battery is at {int(battery.percent)} percent and {status}, sir.")
        else:
            speak("No battery detected, sir.")
        return True

    if action == "get_ram":
        ram = psutil.virtual_memory()
        speak(
            f"Memory usage is at {ram.percent} percent. "
            f"{round(ram.used / 1024**3, 1)} of {round(ram.total / 1024**3, 1)} gigabytes in use, sir."
        )
        return True

    if action == "get_cpu":
        cpu = psutil.cpu_percent(interval=cpu_sample_interval())
        speak(f"CPU usage is at {cpu} percent, sir.")
        return True

    if action == "screenshot":
        folder = os.path.join(os.environ.get("USERPROFILE", ""), "Pictures")
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"jarvis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        delay = desktop_action_delay("JARVIS_SCREENSHOT_DELAY", 0.2)
        if delay:
            time.sleep(delay)
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
        speak("Screenshot saved to your Pictures folder, sir.")
        launch_process(["explorer", f"/select,{file_path}"])
        return True

    if action == "read_clipboard":
        try:
            text = pyperclip.paste()
            if text and text.strip():
                if len(text) > 800:
                    speak("The text is quite long, sir. Reading the first portion.")
                    text = text[:800]
                speak(text)
            else:
                speak("The clipboard is empty, sir.")
        except (OSError, RuntimeError, pyperclip.PyperclipException) as exc:
            logger.exception("Clipboard read failed: %s", exc)
            speak("I couldn't read the clipboard, sir.")
        return True

    if action == "summarize_clipboard":
        try:
            text = pyperclip.paste()
            if text and text.strip():
                summary = summarize_text(text) if callable(summarize_text) else None
                speak(summary or summarize_text_locally(text) or "I had trouble summarizing that, sir.")
            else:
                speak("The clipboard is empty, sir.")
        except (OSError, RuntimeError, pyperclip.PyperclipException) as exc:
            logger.exception("Clipboard summarization failed: %s", exc)
            speak("I couldn't access the clipboard, sir.")
        return True

    if action == "type_text":
        text = params.get("text", "")
        if text:
            delay = desktop_action_delay("JARVIS_TYPE_DELAY", 0.1)
            if delay:
                time.sleep(delay)
            pyautogui.typewrite(text, interval=0.05)
        return True

    if action == "press_key":
        key = params.get("key", "")
        if key:
            if "+" in key:
                pyautogui.hotkey(*key.split("+"))
            else:
                pyautogui.press(key)
        return True

    if action == "mouse_click":
        x = params.get("x", 0)
        y = params.get("y", 0)
        button = params.get("button", "left")
        if button == "double":
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.click(x, y, button=button)
        return True

    if action == "scroll":
        direction = params.get("direction", "down")
        amount = params.get("amount", 3)
        pyautogui.scroll(amount if direction == "up" else -amount)
        return True

    if action == "minimize_all":
        pyautogui.hotkey("win", "d")
        return True

    if action == "maximize_window":
        pyautogui.hotkey("win", "up")
        return True

    if action == "close_window":
        pyautogui.hotkey("alt", "f4")
        return True

    if action == "lock_screen":
        run_command(["rundll32.exe", "user32.dll,LockWorkStation"])
        return True

    if action == "sleep":
        delay = desktop_action_delay("JARVIS_SLEEP_ACTION_DELAY", 1.0)
        if delay:
            time.sleep(delay)
        run_command(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return True

    if action == "shutdown":
        run_command(["shutdown", "/s", "/t", "5"])
        return False

    if action == "restart":
        run_command(["shutdown", "/r", "/t", "5"])
        return False

    return None
