"""Secondary cockpit pages for the JARVIS desktop UI."""

from __future__ import annotations

import os
import socket

import customtkinter as ctk
import psutil

from open_jarvis.health.observability import build_latency_snapshot, build_slo_report
from open_jarvis.integrations.llm_fallback import describe_ai_status
from open_jarvis.runtime.config_runtime import resolved_env
from open_jarvis.ui.security_center import build_security_overview
from open_jarvis.ui.ui_theme import PALETTE, font

PAGE_TITLES = {
    "dashboard": ("DASHBOARD", "Live assistant core and command stream."),
    "system": ("SYSTEM MONITOR", "CPU, memory, disk, network, and microphone readiness."),
    "modules": ("MODULES", "Desktop actions, productivity tools, and command modules."),
    "integrations": ("INTEGRATIONS", "Groq, Spotify, Gemini, weather, and external services."),
    "security": ("SECURITY", "Permission profile, confirmations, safe mode, and secret status."),
    "settings": ("SETTINGS", "Theme, voice, wake word, language, and startup behavior."),
}

PAGE_ITEMS = {
    "system": ["CPU usage", "Memory usage", "Disk status", "Internet status", "Microphone status", "Latency"],
    "modules": ["Application launcher", "Spotify control", "Screenshot capture", "Clipboard reader", "Summarizer", "Mouse and keyboard control"],
    "integrations": ["Groq provider", "Spotify API", "Gemini vision", "Weather service", "Offline fallback", "Local LLM endpoint"],
    "security": ["Confirmation-required commands", "Safe mode", "Dangerous action blocking", "Masked API key status", "Permission profile", "Audit events"],
    "settings": ["Theme", "Accent color", "Voice", "Wake word", "Language", "Startup behavior"],
}


def _mask_status(value: str | None) -> str:
    return "CONFIGURED" if str(value or "").strip() else "MISSING"


def _internet_status() -> str:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=0.2).close()
    except OSError:
        return "OFFLINE"
    return "ONLINE"


def build_info_page(parent, page_key: str) -> ctk.CTkFrame:
    """Build a navigable information page with live value labels."""

    title, subtitle = PAGE_TITLES[page_key]
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame._value_labels = {}  # type: ignore[attr-defined]
    frame._detail_labels = {}  # type: ignore[attr-defined]
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    header = ctk.CTkFrame(frame, fg_color="transparent")
    header.grid(row=0, column=0, padx=92, pady=(86, 18), sticky="ew")
    ctk.CTkLabel(header, text=title, font=font("display", 28, "bold"), text_color=PALETTE["cyan"]).pack(anchor="w")
    ctk.CTkLabel(header, text=subtitle, font=font("mono", 12), text_color=PALETTE["text_muted"]).pack(anchor="w", pady=(8, 0))

    grid = ctk.CTkFrame(frame, fg_color="transparent")
    grid.grid(row=1, column=0, padx=92, pady=(12, 40), sticky="nsew")
    for col in range(3):
        grid.grid_columnconfigure(col, weight=1)
    for index, item in enumerate(PAGE_ITEMS[page_key]):
        card = ctk.CTkFrame(grid, fg_color=PALETTE["surface_glass"], corner_radius=4, border_width=1, border_color=PALETTE["line"])
        card.grid(row=index // 3, column=index % 3, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card, text=item.upper(), font=font("mono", 11, "bold"), text_color=PALETTE["text"]).pack(anchor="w", padx=18, pady=(16, 4))
        value = ctk.CTkLabel(card, text="LOADING", font=font("mono", 16, "bold"), text_color=PALETTE["cyan"])
        value.pack(anchor="w", padx=18, pady=(4, 3))
        detail = ctk.CTkLabel(card, text="Awaiting live telemetry", font=font("mono", 9), text_color=PALETTE["text_muted"])
        detail.pack(anchor="w", padx=18, pady=(0, 16))
        frame._value_labels[item] = value  # type: ignore[attr-defined]
        frame._detail_labels[item] = detail  # type: ignore[attr-defined]
    refresh_info_page(frame, page_key)
    return frame


def refresh_info_pages(pages: dict[str, ctk.CTkFrame]) -> None:
    """Refresh all secondary pages with live runtime data."""

    for page_key, frame in pages.items():
        if page_key != "dashboard":
            refresh_info_page(frame, page_key)


def refresh_info_page(frame: ctk.CTkFrame, page_key: str) -> None:
    """Refresh one secondary page."""

    values = _build_page_values(page_key)
    value_labels = getattr(frame, "_value_labels", {})
    detail_labels = getattr(frame, "_detail_labels", {})
    for item, (value, detail, color) in values.items():
        if item in value_labels:
            value_labels[item].configure(text=value, text_color=color)
        if item in detail_labels:
            detail_labels[item].configure(text=detail)


def _build_page_values(page_key: str) -> dict[str, tuple[str, str, str]]:
    env = resolved_env(os.environ)
    if page_key == "system":
        disk = psutil.disk_usage(os.getcwd())
        latency = build_latency_snapshot()
        return {
            "CPU usage": (f"{psutil.cpu_percent():.0f}%", "Live processor load", PALETTE["cyan"]),
            "Memory usage": (f"{psutil.virtual_memory().percent:.0f}%", "System RAM in use", PALETTE["cyan"]),
            "Disk status": (f"{disk.percent:.0f}%", "Workspace drive usage", PALETTE["cyan"]),
            "Internet status": (_internet_status(), "Fast connectivity probe", PALETTE["green"]),
            "Microphone status": ("READY", "SpeechRecognition runtime installed", PALETTE["green"]),
            "Latency": (f"{latency['average_ms']}ms", f"{latency['count']} recent samples", PALETTE["amber"]),
        }
    if page_key == "modules":
        return {
            "Application launcher": ("READY", "Browser, Chrome, Edge, VS Code, Calculator", PALETTE["green"]),
            "Spotify control": ("OPTIONAL", "Requires Spotify credentials for API control", PALETTE["amber"]),
            "Screenshot capture": ("READY", "Desktop screenshot workflow available", PALETTE["green"]),
            "Clipboard reader": ("READY", "Read and summarize copied text", PALETTE["green"]),
            "Summarizer": ("READY", "Rules plus AI fallback when configured", PALETTE["green"]),
            "Mouse and keyboard control": ("GUARDED", "Risky automation requires confirmation", PALETTE["amber"]),
        }
    if page_key == "integrations":
        ai = describe_ai_status(env)
        return {
            "Groq provider": (_mask_status(env.get("GROQ_API_KEY")), ai["reason"], PALETTE["green"] if env.get("GROQ_API_KEY") else PALETTE["amber"]),
            "Spotify API": (_mask_status(env.get("SPOTIFY_CLIENT_ID")), "Client ID and secret stay masked", PALETTE["green"] if env.get("SPOTIFY_CLIENT_ID") else PALETTE["amber"]),
            "Gemini vision": (_mask_status(env.get("GEMINI_API_KEY")), "Optional vision provider", PALETTE["green"] if env.get("GEMINI_API_KEY") else PALETTE["amber"]),
            "Weather service": ("LOCAL READY", "Uses configured command tooling when enabled", PALETTE["cyan"]),
            "Offline fallback": ("OFF" if env.get("JARVIS_OFFLINE_STT") != "1" else "ON", "Vosk fallback is optional", PALETTE["amber"]),
            "Local LLM endpoint": (_mask_status(env.get("JARVIS_LOCAL_LLM_URL")), ai["mode"], PALETTE["cyan"]),
        }
    if page_key == "security":
        overview = build_security_overview(env, actions=["shutdown", "restart", "lock_screen", "type_text", "press_key", "open_web"])
        profile = overview["profile"]
        matrix = overview["permission_matrix"]
        blocked = sum(1 for status in matrix["shutdown"].values() if status == "blocked")
        report = build_slo_report()
        configured = sum(1 for status in overview["secrets"].values() if status == "CONFIGURED")
        return {
            "Confirmation-required commands": (str(len(overview["confirmation_required"])), "Risky desktop actions require approval", PALETTE["green"]),
            "Safe mode": ("ON" if profile["id"] == "safe" else "OFF", f"Privacy: {overview['privacy']['retention']}", PALETTE["amber"]),
            "Dangerous action blocking": ("ENABLED", f"Shutdown blocked in {blocked} profiles", PALETTE["green"]),
            "Masked API key status": ("MASKED", f"{configured} optional secrets configured", PALETTE["green"]),
            "Permission profile": (profile["label"], "Allowed actions are policy-controlled", PALETTE["cyan"]),
            "Audit events": (str(report["events_seen"]), f"{report['warning_count']} warnings, {report['error_count']} errors", PALETTE["amber"]),
        }
    return {
        "Theme": ("CYBER HUD", "Dark blue-black cockpit", PALETTE["cyan"]),
        "Accent color": (PALETTE["cyan"], "Primary reactor glow", PALETTE["cyan"]),
        "Voice": (env.get("JARVIS_TTS_PROVIDER", "edge").upper(), "TTS provider", PALETTE["cyan"]),
        "Wake word": (env.get("JARVIS_WAKE_WORD", "jarvis").upper(), "Assistant activation phrase", PALETTE["cyan"]),
        "Language": (env.get("JARVIS_LANGUAGE", "EN").upper(), "Voice command language setting", PALETTE["cyan"]),
        "Startup behavior": ("ONBOARDING" if not env.get("JARVIS_ONBOARDING_COMPLETE") else "READY", "First-run setup gate", PALETTE["amber"]),
    }
