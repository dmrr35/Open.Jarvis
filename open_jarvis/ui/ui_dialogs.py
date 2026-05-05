"""Dialog windows used by the JARVIS desktop UI."""

from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from open_jarvis.health.health_center import apply_safe_health_fixes, build_health_center
from open_jarvis.health.observability import build_runtime_event_snapshot
from open_jarvis.memory import build_memory_health_report, load_memory
from open_jarvis.security.jarvis_admin import (
    build_env_template,
    build_health_checks,
    build_settings_guide,
    read_env_settings,
    render_health_report,
    write_env_settings,
)
from open_jarvis.ui.memory_panel import build_memory_panel
from open_jarvis.ui.ui_theme import PALETTE, font

BG = PALETTE["bg"]
BG2 = PALETTE["bg_elevated"]
BLUE = PALETTE["cyan"]
BLUE2 = PALETTE["blue"]
BLUE_DIM = PALETTE["surface_soft"]
GREEN = PALETTE["green"]
TEXT_DIM = PALETTE["text_muted"]
CARD = PALETTE["surface"]
LINE = PALETTE["line"]


def load_readme_preview(path: Path | None = None, max_chars: int = 12000) -> str:
    """Load a bounded README preview for the in-app documentation viewer."""

    readme_path = path or Path(__file__).resolve().parent / "README.md"
    if not readme_path.exists():
        return "README.md was not found in the project root."
    content = readme_path.read_text(encoding="utf-8")
    if len(content) <= max_chars:
        return content
    return content[:max_chars].rstrip() + "\n\n[Preview truncated. Open README.md for the full document.]"


def build_health_center_text(checks: list[dict] | None = None) -> str:
    """Render a concise health-center report for the desktop UI."""

    center = build_health_center(checks or build_health_checks())
    summary = center["summary"]
    lines = [
        "Health Center",
        (
            f"Critical: {summary['critical']}  Warning: {summary['warning']}  "
            f"Info: {summary['info']}  OK: {summary['ok']}  Safe fixes: {summary['safe_fixes']}"
        ),
        "",
    ]
    for item in center["checks"]:
        lines.append(f"[{item['severity'].upper()}] {item['title']}")
        if item.get("detail"):
            lines.append(f"  Detail: {item['detail']}")
        if item.get("fix"):
            lines.append(f"  Fix: {item['fix']}")
        if item.get("fix_command"):
            lines.append(f"  Command: {item['fix_command']}")
        fix_plan = item.get("fix_plan") or {}
        lines.append(f"  Fix mode: {fix_plan.get('mode', 'manual')}")
        if fix_plan.get("available"):
            lines.append(f"  Dry run: {fix_plan.get('dry_run')}")
        lines.append("")
    return "\n".join(lines).strip()


def build_memory_view_text() -> str:
    """Render current memory state without exposing implementation details."""

    memory = load_memory()
    panel = build_memory_panel(memory)
    health = build_memory_health_report(memory)
    lines = [
        "Memory Center",
        f"Quality score: {health.get('score', 'unknown')}",
        f"Preferences: {panel['counts']['preferences']}  Notes: {panel['counts']['notes']}  Habits: {panel['counts']['habits']}",
        "",
        "Preferences",
    ]
    if panel["preferences"]:
        lines.extend(f"- {key}: {value}" for key, value in panel["preferences"].items())
    else:
        lines.append("- No preferences saved yet.")
    lines.append("")
    lines.append("Notes")
    if panel["notes"]:
        lines.extend(f"- {note}" for note in panel["notes"][:20])
    else:
        lines.append("- No notes saved yet.")
    lines.append("")
    lines.append("Top habits")
    if panel["habits"]:
        for command, count in sorted(panel["habits"].items(), key=lambda item: item[1], reverse=True)[:20]:
            lines.append(f"- {command}: {count}")
    else:
        lines.append("- No habits tracked yet.")
    return "\n".join(lines)


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, on_saved=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.title("JARVIS Settings")
        self.geometry("1080x720")
        self.configure(fg_color=BG)
        self.grab_set()

        self._entries = {}
        self._health_box = None
        self._status_label = None
        self._build_ui()
        self._load_values()
        self._refresh_health()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="SETTINGS", font=font("display", 20, "bold"), text_color=BLUE).grid(
            row=0, column=0, padx=18, pady=(16, 2), sticky="w"
        )
        ctk.CTkLabel(
            header,
            text="Settings are read from .env and can be edited here with safe defaults.",
            font=font("ui", 11),
            text_color=TEXT_DIM,
        ).grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, padx=18, pady=16, sticky="e")
        ctk.CTkButton(actions, text="Copy template", fg_color=BLUE_DIM, command=self._copy_template).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Refresh health", fg_color=BLUE_DIM, command=self._refresh_health).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Save", fg_color=GREEN, text_color="#00140a", command=self._save).pack(side="left", padx=4)

        left = ctk.CTkFrame(self, fg_color=BG2, corner_radius=28, border_width=1, border_color=LINE)
        left.grid(row=1, column=0, padx=(18, 9), pady=18, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        scroll.grid_columnconfigure(1, weight=1)

        for index, item in enumerate(build_settings_guide()):
            row = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=18, border_width=1, border_color=LINE)
            row.grid(row=index, column=0, sticky="ew", pady=6)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=item["key"], font=font("mono", 11, "bold"), text_color=BLUE).grid(
                row=0, column=0, padx=12, pady=(10, 2), sticky="w"
            )
            ctk.CTkLabel(row, text=f"Safe default: {item['safe_default']}", font=font("mono", 9), text_color=TEXT_DIM).grid(
                row=0, column=1, padx=12, pady=(10, 2), sticky="e"
            )
            ctk.CTkLabel(
                row, text=item["description"], font=font("ui", 11), text_color=PALETTE["text"], wraplength=420, justify="left"
            ).grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 8), sticky="w")
            entry = ctk.CTkEntry(row, placeholder_text=item["default"], font=font("mono", 11), corner_radius=12)
            entry.grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")
            self._entries[item["key"]] = entry

        right = ctk.CTkFrame(self, fg_color=BG2, corner_radius=28, border_width=1, border_color=LINE)
        right.grid(row=1, column=1, padx=(9, 18), pady=18, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Health Preview", font=font("display", 15, "bold"), text_color=BLUE).grid(
            row=0, column=0, padx=14, pady=(14, 6), sticky="w"
        )
        self._health_box = ctk.CTkTextbox(right, fg_color="transparent", font=font("mono", 11), wrap="word")
        self._health_box.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")
        self._health_box.configure(state="disabled")

        self._status_label = ctk.CTkLabel(right, text="", font=font("ui", 11), text_color=TEXT_DIM, wraplength=360, justify="left")
        self._status_label.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="w")

        footer = ctk.CTkFrame(right, fg_color="transparent")
        footer.grid(row=3, column=0, padx=14, pady=(0, 14), sticky="ew")
        ctk.CTkButton(footer, text="Close", fg_color="#4a1f1f", command=self._close).pack(side="right")

    def _load_values(self):
        settings = read_env_settings()
        for key, entry in self._entries.items():
            entry.delete(0, "end")
            entry.insert(0, settings.get(key, ""))

    def _current_settings(self):
        return {key: entry.get().strip() for key, entry in self._entries.items()}

    def _refresh_health(self):
        current = self._current_settings()
        checks = build_health_checks(env=current)
        report = render_health_report(checks)
        self._health_box.configure(state="normal")
        self._health_box.delete("1.0", "end")
        self._health_box.insert("end", report)
        self._health_box.configure(state="disabled")
        self._status_label.configure(
            text="Changes are saved to .env. Runtime-sensitive values like the wake word and microphone threshold take effect after restarting JARVIS."
        )

    def _copy_template(self):
        self.clipboard_clear()
        self.clipboard_append(build_env_template())
        self._status_label.configure(text="Copied the recommended .env template.")

    def _save(self):
        settings = self._current_settings()
        write_env_settings(settings)
        os.environ.update(settings)
        self._refresh_health()
        if self.on_saved:
            self.on_saved(settings)
        self._status_label.configure(text="Saved settings to .env. Restart JARVIS to apply runtime-sensitive changes.")

    def _close(self):
        self.grab_release()
        self.destroy()


class RuntimeLogDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("JARVIS Runtime Logs")
        self.geometry("960x680")
        self.configure(fg_color=BG)
        self.grab_set()

        self._severity_var = tk.StringVar(value="all")
        self._summary_label = None
        self._box = None
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="RUNTIME LOGS", font=font("display", 20, "bold"), text_color=BLUE).grid(
            row=0, column=0, padx=18, pady=(16, 2), sticky="w"
        )
        self._summary_label = ctk.CTkLabel(header, text="", font=font("ui", 11), text_color=TEXT_DIM)
        self._summary_label.grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, padx=18, pady=16, sticky="e")
        ctk.CTkLabel(actions, text="Severity", font=font("mono", 9, "bold"), text_color=TEXT_DIM).pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(
            actions,
            values=["all", "critical", "warning", "info", "ok"],
            variable=self._severity_var,
            fg_color=BLUE_DIM,
            button_color=BLUE2,
            button_hover_color=BLUE,
            command=self._on_filter_changed,
            width=130,
        ).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Refresh", fg_color=BLUE_DIM, command=self._refresh).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Close", fg_color="#4a1f1f", command=self._close).pack(side="left", padx=4)

        body = ctk.CTkFrame(self, fg_color=BG2, corner_radius=28, border_width=1, border_color=LINE)
        body.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._box = ctk.CTkTextbox(body, fg_color="transparent", font=font("mono", 11), wrap="word")
        self._box.grid(row=0, column=0, padx=14, pady=14, sticky="nsew")
        self._box.configure(state="disabled")

    def _on_filter_changed(self, _selected=None):
        self._refresh()

    def _refresh(self):
        snapshot = build_runtime_event_snapshot(limit=40, severity=self._severity_var.get())
        report = snapshot["report"]
        self._summary_label.configure(text=snapshot["summary"])

        self._box.configure(state="normal")
        self._box.delete("1.0", "end")

        if not snapshot["events"]:
            self._box.insert("end", "No runtime events have been recorded yet.\n")
        else:
            self._box.insert("end", f"Runtime posture: {report['status']}\n")
            self._box.insert("end", f"Recommendation: {report['recommendation']}\n\n")
            for event in snapshot["formatted_events"]:
                self._box.insert("end", event + "\n\n")

        self._box.configure(state="disabled")
        self._box.see("1.0")

    def _close(self):
        self.grab_release()
        self.destroy()


class ReadmeDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("JARVIS README")
        self.geometry("1040x720")
        self.configure(fg_color=BG)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="README", font=font("display", 20, "bold"), text_color=BLUE).grid(
            row=0, column=0, padx=18, pady=(16, 2), sticky="w"
        )
        ctk.CTkLabel(
            header,
            text="Project documentation is shown inside JARVIS so first-run setup stays polished.",
            font=font("ui", 11),
            text_color=TEXT_DIM,
        ).grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")
        ctk.CTkButton(header, text="Close", fg_color="#4a1f1f", command=self._close).grid(row=0, column=1, rowspan=2, padx=18, pady=16)

        body = ctk.CTkFrame(self, fg_color=CARD, corner_radius=28, border_width=1, border_color=LINE)
        body.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._box = ctk.CTkTextbox(body, fg_color="transparent", font=font("mono", 11), wrap="word")
        self._box.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self._box.insert("end", load_readme_preview())
        self._box.configure(state="disabled")

    def _close(self):
        self.grab_release()
        self.destroy()


class HealthCenterDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("JARVIS Health Center")
        self.geometry("1000x700")
        self.configure(fg_color=BG)
        self.grab_set()
        self._box = None
        self._status_label = None
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="HEALTH CENTER", font=font("display", 20, "bold"), text_color=BLUE).grid(
            row=0, column=0, padx=18, pady=(16, 2), sticky="w"
        )
        ctk.CTkLabel(header, text="Prioritized checks with concrete remediation commands.", font=font("ui", 11), text_color=TEXT_DIM).grid(
            row=1, column=0, padx=18, pady=(0, 16), sticky="w"
        )
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, padx=18, pady=16, sticky="e")
        ctk.CTkButton(actions, text="Refresh", fg_color=BLUE_DIM, command=self._refresh).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Dry Run Fixes", fg_color=BLUE_DIM, command=self._dry_run_fixes).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Apply Safe Fixes", fg_color=GREEN, text_color=BG, command=self._apply_safe_fixes).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Close", fg_color="#4a1f1f", command=self._close).pack(side="left", padx=4)

        body = ctk.CTkFrame(self, fg_color=CARD, corner_radius=28, border_width=1, border_color=LINE)
        body.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self._box = ctk.CTkTextbox(body, fg_color="transparent", font=font("mono", 11), wrap="word")
        self._box.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self._box.configure(state="disabled")
        self._status_label = ctk.CTkLabel(body, text="", font=font("ui", 11), text_color=TEXT_DIM, anchor="w")
        self._status_label.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")

    def _refresh(self):
        self._box.configure(state="normal")
        self._box.delete("1.0", "end")
        self._box.insert("end", build_health_center_text())
        self._box.configure(state="disabled")
        self._box.see("1.0")

    def _run_safe_fixes(self, *, dry_run: bool):
        center = build_health_center(build_health_checks())
        result = apply_safe_health_fixes(center, dry_run=dry_run)
        mode = "Dry run" if dry_run else "Applied"
        details = ", ".join(f"{item['fix_id']}={item['status']}" for item in result["results"]) or "no safe fixes available"
        self._status_label.configure(text=f"{mode}: {details}")
        self._refresh()

    def _dry_run_fixes(self):
        self._run_safe_fixes(dry_run=True)

    def _apply_safe_fixes(self):
        self._run_safe_fixes(dry_run=False)

    def _close(self):
        self.grab_release()
        self.destroy()


class MemoryViewerDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("JARVIS Memory Center")
        self.geometry("1000x700")
        self.configure(fg_color=BG)
        self.grab_set()
        self._box = None
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="MEMORY CENTER", font=font("display", 20, "bold"), text_color=BLUE).grid(
            row=0, column=0, padx=18, pady=(16, 2), sticky="w"
        )
        ctk.CTkLabel(
            header,
            text="A safe, readable view of preferences, notes, habits, and memory health.",
            font=font("ui", 11),
            text_color=TEXT_DIM,
        ).grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, padx=18, pady=16, sticky="e")
        ctk.CTkButton(actions, text="Refresh", fg_color=BLUE_DIM, command=self._refresh).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Close", fg_color="#4a1f1f", command=self._close).pack(side="left", padx=4)

        body = ctk.CTkFrame(self, fg_color=CARD, corner_radius=28, border_width=1, border_color=LINE)
        body.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self._box = ctk.CTkTextbox(body, fg_color="transparent", font=font("mono", 11), wrap="word")
        self._box.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        self._box.configure(state="disabled")

    def _refresh(self):
        self._box.configure(state="normal")
        self._box.delete("1.0", "end")
        self._box.insert("end", build_memory_view_text())
        self._box.configure(state="disabled")
        self._box.see("1.0")

    def _close(self):
        self.grab_release()
        self.destroy()
