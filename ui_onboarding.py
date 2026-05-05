"""First-run onboarding wizard for Open.Jarvis."""

from __future__ import annotations

import customtkinter as ctk

from jarvis_admin import (
    build_env_template,
    build_onboarding_steps,
    build_settings_guide,
    save_setup_state,
    should_show_onboarding,
)
from ui_dialogs import ReadmeDialog
from ui_theme import PALETTE, font

BG = PALETTE["bg"]
BG2 = PALETTE["bg_elevated"]
BLUE = PALETTE["cyan"]
BLUE_DIM = PALETTE["surface_soft"]
GREEN = PALETTE["green"]
AMBER = PALETTE["amber"]
RED = PALETTE["red"]
TEXT_DIM = PALETTE["text_muted"]
LINE = PALETTE["line"]


class OnboardingWizard(ctk.CTkToplevel):
    """Simple modal onboarding flow with checks and one-click fixes."""

    def __init__(self, master, on_complete=None):
        super().__init__(master)
        self.on_complete = on_complete
        self.title("JARVIS Setup Wizard")
        self.geometry("1120x740")
        self.configure(fg_color=BG)
        self.resizable(True, True)
        self.grab_set()

        self._log_messages = []
        self._build_ui()
        self._render()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="JARVIS FIRST-RUN SETUP",
            font=font("display", 22, "bold"),
            text_color=BLUE,
        ).grid(row=0, column=0, padx=18, pady=18, sticky="w")

        ctk.CTkLabel(
            header,
            text="Review Groq, Spotify, Gemini, voice output, microphone, and privacy settings before first launch.",
            font=font("ui", 11),
            text_color=TEXT_DIM,
        ).grid(row=1, column=0, padx=18, pady=(0, 18), sticky="w")

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.grid(row=0, column=1, rowspan=2, padx=18, pady=18, sticky="e")
        ctk.CTkButton(
            controls,
            text="Copy .env template",
            fg_color=BLUE_DIM,
            hover_color="#004c7a",
            command=self._copy_env_template,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            controls,
            text="Open README",
            fg_color=BLUE_DIM,
            hover_color="#004c7a",
            command=self._open_readme,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            controls,
            text="Finish setup",
            fg_color=GREEN,
            hover_color="#00cc66",
            text_color="#00140a",
            command=self._finish,
        ).pack(side="left", padx=4)

        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, fg_color=BG2, corner_radius=28, border_width=1, border_color=LINE)
        left.grid(row=0, column=0, padx=(18, 9), pady=18, sticky="nsew")
        left.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(left, text="Connection checks", font=font("display", 15, "bold"), text_color=BLUE).pack(
            anchor="w", padx=16, pady=(16, 6)
        )
        self._checks_box = ctk.CTkTextbox(left, fg_color="transparent", font=font("mono", 11), height=220, wrap="word")
        self._checks_box.pack(fill="both", expand=False, padx=16, pady=(0, 12))
        self._checks_box.configure(state="disabled")

        ctk.CTkLabel(left, text="Settings guide", font=font("display", 15, "bold"), text_color=BLUE).pack(anchor="w", padx=16, pady=(8, 6))
        self._settings_box = ctk.CTkTextbox(left, fg_color="transparent", font=font("mono", 11), wrap="word")
        self._settings_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._settings_box.configure(state="disabled")

        right = ctk.CTkFrame(body, fg_color=BG2, corner_radius=28, border_width=1, border_color=LINE)
        right.grid(row=0, column=1, padx=(9, 18), pady=18, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(right, text="Fix suggestions", font=font("display", 15, "bold"), text_color=BLUE).pack(
            anchor="w", padx=16, pady=(16, 6)
        )
        self._fix_box = ctk.CTkTextbox(right, fg_color="transparent", font=font("mono", 11), wrap="word")
        self._fix_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self._fix_box.configure(state="disabled")

        footer = ctk.CTkFrame(right, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(footer, text="Recheck", fg_color=BLUE_DIM, hover_color="#004c7a", command=self._render).pack(side="left")
        ctk.CTkButton(footer, text="Skip for now", fg_color="#4a1f1f", hover_color="#7a2a2a", command=self._skip).pack(side="right")

    def _render(self):
        steps = build_onboarding_steps()
        settings = build_settings_guide()

        self._replace_box(
            self._checks_box,
            self._format_checks(steps),
        )
        self._replace_box(
            self._settings_box,
            self._format_settings(settings),
        )
        self._replace_box(
            self._fix_box,
            self._format_fixes(steps),
        )

    def _format_checks(self, steps):
        lines = []
        for item in steps:
            status = item["status"].upper()
            lines.append(f"[{status}] {item['title']}")
            lines.append(f"  {item['detail']}")
            lines.append("")
        return "\n".join(lines).strip()

    def _format_settings(self, settings):
        lines = []
        for item in settings:
            lines.append(f"{item['key']}  | safe default: {item['safe_default']}")
            lines.append(f"  {item['description']}")
            lines.append("")
        return "\n".join(lines).strip()

    def _format_fixes(self, steps):
        lines = [
            "Recommended next actions:",
            "",
        ]
        for item in steps:
            lines.append(f"- {item['title']}: {item['fix']}")
        lines.append("")
        lines.append("You can copy the recommended .env template and fill it in once.")
        return "\n".join(lines)

    def _replace_box(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.configure(state="disabled")

    def _copy_env_template(self):
        self.clipboard_clear()
        self.clipboard_append(build_env_template())
        self._log_messages.append("Copied recommended .env template.")

    def _open_readme(self):
        ReadmeDialog(self)

    def _finish(self):
        save_setup_state({"source": "onboarding_wizard"})
        self.grab_release()
        self.destroy()
        if self.on_complete:
            self.on_complete()

    def _skip(self):
        self.grab_release()
        self.destroy()
        if self.on_complete:
            self.on_complete()


def show_onboarding(master, on_complete=None):
    """Show the onboarding wizard only when needed."""

    if not should_show_onboarding():
        if on_complete:
            on_complete()
        return None
    return OnboardingWizard(master, on_complete=on_complete)
