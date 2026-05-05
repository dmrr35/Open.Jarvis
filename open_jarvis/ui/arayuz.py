"""JARVIS desktop UI - cyber hologram interface."""

from __future__ import annotations

import datetime
import math
import os
import threading
import time

import customtkinter as ctk
import psutil

from open_jarvis.app.main import set_ui_callback, start_jarvis
from open_jarvis.health.observability import build_latency_snapshot, build_slo_report
from open_jarvis.integrations.llm_fallback import describe_ai_status
from open_jarvis.plugins.permission_profiles import get_active_permission_profile
from open_jarvis.ui.ui_hud_effects import (
    add_terminal_corners,
    draw_background_depth,
    draw_equalizer,
    draw_mini_orb,
    draw_sidebar_dots,
    draw_waveform,
)
from open_jarvis.ui.ui_log_events import infer_log_kind, normalize_log_event
from open_jarvis.ui.ui_navigation import build_sidebar, refresh_sidebar
from open_jarvis.ui.ui_onboarding import show_onboarding
from open_jarvis.ui.ui_pages import PAGE_TITLES, build_info_page, refresh_info_pages
from open_jarvis.ui.ui_rendering import draw_hologram_figure
from open_jarvis.ui.ui_state import get_state_profile, infer_state_from_message
from open_jarvis.ui.ui_theme import PALETTE, font

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG = PALETTE["bg"]
PANEL = PALETTE["surface"]
TERMINAL_BG = PALETTE["surface_glass"]
BLUE = PALETTE["cyan"]
BLUE_DIM = PALETTE["surface_soft"]
SOFT_LINE = PALETTE["line_soft"]
GREEN = PALETTE["green"]
AMBER = PALETTE["amber"]
RED = PALETTE["red"]
TEXT_DIM = PALETTE["text_muted"]
TEXT = PALETTE["text"]
LINE = PALETTE["line"]
STARTUP_GREETING = "Good day. All systems are ready."

class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JARVIS Cyber Interface")
        self.geometry("1600x900")
        self.minsize(1366, 768)
        self.configure(fg_color=BG)
        self.resizable(True, True)

        self._cmd_count = 0
        self._start_time = time.time()
        self._drag_x = 0
        self._drag_y = 0
        self._jarvis_started = False
        self._runtime_value_labels = {}
        self._runtime_status_label = None
        self._runtime_count_label = None
        self._runtime_latency_label = None
        self._ring_angle = 0
        self._signal_phase = 0.0
        self._sidebar_phase = 0.0
        self._mini_orb_phase = 0.0
        self._assistant_state = "BOOTING"
        self._state_profile = get_state_profile("BOOTING")
        self._pages, self._nav_canvases = {}, {}
        self._active_page = "dashboard"
        self._hover_page = None

        self._build_ui()
        self.set_assistant_state("BOOTING", log_event=False)
        self.after(900, lambda: self.set_assistant_state("STANDBY", log_event=False) if self._assistant_state == "BOOTING" else None)
        self._start_updates()
        self._start_onboarding_or_jarvis()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._shell = ctk.CTkFrame(self, fg_color=BG, corner_radius=12, border_width=1, border_color=LINE)
        self._shell.grid(row=0, column=0, padx=10, pady=8, sticky="nsew")
        self._shell.grid_columnconfigure(0, weight=1)
        self._shell.grid_rowconfigure(1, weight=1)
        self._build_titlebar()
        self._build_center_stage()
        self._build_bottombar()

    def _build_titlebar(self):
        bar = ctk.CTkFrame(self._shell, fg_color=BG, corner_radius=12, height=48, border_width=1, border_color=SOFT_LINE)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.grid(row=0, column=0, padx=24, pady=8, sticky="w")
        self._draw_mini_orb(brand, size=24).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(
            brand,
            text="JARVIS CYBER INTERFACE",
            font=font("display", 12, "bold"),
            text_color=TEXT,
        ).pack(side="left")

        self._date_label = ctk.CTkLabel(
            bar,
            text="INITIALIZING",
            font=font("mono", 10, "bold"),
            text_color=TEXT_DIM,
            fg_color=PANEL,
            corner_radius=999,
            width=170,
            padx=18,
            pady=7,
        )
        self._date_label.grid(row=0, column=1, pady=8)

        controls = ctk.CTkFrame(bar, fg_color="transparent")
        controls.grid(row=0, column=2, padx=18, pady=6, sticky="e")
        for text, command in [("-", self.iconify), ("[]", self._toggle_maximize), ("X", self.destroy)]:
            ctk.CTkButton(
                controls,
                text=text,
                width=36,
                height=28,
                fg_color="#07101C",
                hover_color=BLUE_DIM,
                border_width=1,
                border_color=BLUE,
                corner_radius=5,
                font=font("ui", 14, "bold"),
                text_color=BLUE,
                command=command,
            ).pack(side="left", padx=5)

        bar.bind("<ButtonPress-1>", self._drag_start)
        bar.bind("<B1-Motion>", self._drag_move)
        self._date_label.bind("<ButtonPress-1>", self._drag_start)
        self._date_label.bind("<B1-Motion>", self._drag_move)

    def _build_center_stage(self):
        stage = ctk.CTkFrame(self._shell, fg_color=BG, corner_radius=0)
        stage.grid(row=1, column=0, sticky="nsew")
        stage.grid_columnconfigure(1, weight=1)
        stage.grid_rowconfigure(0, weight=1)

        self._build_sidebar(stage)

        content = ctk.CTkFrame(stage, fg_color=BG, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.bind("<Configure>", self._draw_background)
        self._background = ctk.CTkCanvas(content, bg=BG, highlightthickness=0)
        self._background.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._content = content
        self._dashboard_page = ctk.CTkFrame(content, fg_color="transparent")
        self._dashboard_page.grid(row=0, column=0, sticky="nsew")
        self._dashboard_page.grid_columnconfigure(0, weight=1)

        title_stack = ctk.CTkFrame(self._dashboard_page, fg_color="transparent")
        title_stack.place(x=34, y=34)
        ctk.CTkLabel(title_stack, text="J.A.R.V.I.S", font=font("display", 18, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkFrame(title_stack, fg_color=BLUE, width=52, height=2).pack(anchor="w", pady=(9, 0))
        ctk.CTkFrame(title_stack, fg_color=LINE, width=170, height=1).pack(anchor="w")
        ctk.CTkLabel(
            title_stack,
            text="CYBER HOLOGRAM INTERFACE",
            font=font("mono", 10, "bold"),
            text_color=TEXT_DIM,
        ).pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(title_stack, text="CORE READY", font=font("mono", 8, "bold"), text_color=GREEN).pack(anchor="w", pady=(7, 0))

        top_spacer = ctk.CTkFrame(self._dashboard_page, fg_color="transparent", height=12)
        top_spacer.grid(row=0, column=0, sticky="ew")

        self._canvas = ctk.CTkCanvas(self._dashboard_page, width=620, height=430, bg=BG, highlightthickness=0)
        self._canvas.grid(row=1, column=0, pady=(0, 0))
        self._draw_hologram()

        self._title_label = ctk.CTkLabel(
            self._dashboard_page,
            text="J A R V I S",
            font=font("display", 58, "bold"),
            text_color=BLUE,
        )
        self._title_label.grid(row=2, column=0, pady=(4, 4))

        self._subtitle_label = ctk.CTkLabel(
            self._dashboard_page,
            text="I am a virtual assistant JARVIS, how may I help you?",
            font=font("mono", 14),
            text_color=TEXT_DIM,
        )
        self._subtitle_label.grid(row=3, column=0, pady=(0, 16))

        status_line = ctk.CTkFrame(self._dashboard_page, fg_color="transparent")
        status_line.grid(row=4, column=0, pady=(0, 10))
        ctk.CTkFrame(status_line, fg_color=LINE, width=58, height=1).pack(side="left", padx=(0, 20), pady=9)

        self._status_label = ctk.CTkLabel(
            status_line,
            text="STANDBY - SAY JARVIS",
            font=font("mono", 11, "bold"),
            text_color=BLUE,
        )
        self._status_label.pack(side="left")
        ctk.CTkFrame(status_line, fg_color=LINE, width=58, height=1).pack(side="left", padx=(20, 0), pady=9)

        log_frame = ctk.CTkFrame(self._dashboard_page, fg_color=TERMINAL_BG, corner_radius=3, border_width=1, border_color=LINE)
        log_frame.grid(row=5, column=0, padx=90, pady=(0, 14), sticky="ew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_columnconfigure(1, weight=0)
        add_terminal_corners(log_frame, accent=BLUE)

        self._log_box = ctk.CTkTextbox(
            log_frame,
            height=94,
            fg_color="transparent",
            font=font("mono", 10),
            text_color="#74eaff",
            activate_scrollbars=True,
            wrap="word",
        )
        self._log_box.grid(row=0, column=0, padx=12, pady=(22, 8), sticky="ew")
        self._log_box.configure(state="disabled")
        self._equalizer = ctk.CTkCanvas(log_frame, width=190, height=76, bg=TERMINAL_BG, highlightthickness=0)
        self._equalizer.grid(row=0, column=1, padx=(0, 34), pady=18)
        self._draw_equalizer()
        ctk.CTkLabel(log_frame, text="COMMAND STREAM", font=font("mono", 8, "bold"), text_color=TEXT_DIM, fg_color=TERMINAL_BG).place(x=30, y=5)

        self._add_log("JARVIS initialized", "info")
        self._add_log("Voice recognition active", "voice")
        self._add_log(STARTUP_GREETING, "ok")
        self._pages["dashboard"] = self._dashboard_page
        for page_key in ["system", "modules", "integrations", "security", "settings"]:
            self._pages[page_key] = build_info_page(content, page_key)
        self._show_page("dashboard")

    def _build_bottombar(self):
        bar = ctk.CTkFrame(self._shell, fg_color=BG, corner_radius=0, height=84, border_width=1, border_color=LINE)
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_propagate(False)
        for column, weight in [(0, 0), (1, 0), (2, 1), (3, 0), (4, 0)]:
            bar.grid_columnconfigure(column, weight=weight)

        status = ctk.CTkFrame(bar, fg_color="transparent")
        status.grid(row=0, column=0, padx=24, pady=8, sticky="w")
        ctk.CTkLabel(status, text="+  SYSTEM STATUS", font=font("mono", 8, "bold"), text_color=TEXT_DIM).pack(anchor="w")
        ctk.CTkLabel(status, text="ALL SYSTEMS OPERATIONAL", font=font("mono", 8, "bold"), text_color=BLUE).pack(anchor="w", pady=(6, 0))
        ctk.CTkFrame(bar, fg_color=SOFT_LINE, width=1, height=52).grid(row=0, column=1, sticky="w", pady=14)

        telemetry = ctk.CTkFrame(bar, fg_color="transparent")
        telemetry.grid(row=0, column=1, padx=34, pady=8, sticky="w")
        self._clock_label = self._mini_value(telemetry, "TIME", "00:00:00", BLUE)
        self._cpu_label = self._mini_value(telemetry, "CPU", "--%", AMBER)
        self._ram_label = self._mini_value(telemetry, "MEMORY", "--%", AMBER)
        self._gpu_label = self._mini_value(telemetry, "GPU", "N/A", TEXT_DIM)

        self._wave_canvas = ctk.CTkCanvas(bar, width=230, height=48, bg=BG, highlightthickness=1, highlightbackground=LINE)
        self._wave_canvas.grid(row=0, column=2, padx=20, pady=12)
        self._draw_waveform()
        ctk.CTkFrame(bar, fg_color=SOFT_LINE, width=1, height=52).grid(row=0, column=3, sticky="w", pady=14)

        runtime = ctk.CTkFrame(bar, fg_color="transparent")
        runtime.grid(row=0, column=3, padx=24, pady=8, sticky="e")
        ai_status = describe_ai_status(os.environ)
        permission = get_active_permission_profile(os.environ)
        self._runtime_value_labels["permission_profile"] = self._mini_value(runtime, "PERMISSION", permission["label"], GREEN)
        self._runtime_status_label = self._mini_value(runtime, "POSTURE", build_slo_report()["status"].upper(), GREEN)
        self._runtime_count_label = self._mini_value(runtime, "EVENTS", f"{build_slo_report()['events_seen']}", BLUE)
        self._runtime_latency_label = self._mini_value(runtime, "LATENCY", f"{build_latency_snapshot()['average_ms']}ms", AMBER)
        self._cmd_label = self._mini_value(runtime, "COMMANDS", "0", BLUE)
        self._uptime_label = self._mini_value(runtime, "UPTIME", "00:00:00", AMBER)
        self._runtime_value_labels["ai_provider"] = self._mini_value(runtime, "AI", ai_status["provider"], BLUE)
        self._bottom_orb = self._draw_mini_orb(bar, size=58)
        self._bottom_orb.grid(row=0, column=4, padx=(8, 28), pady=8)
        self._draw_bottom_reactor()

    def _build_sidebar(self, parent):
        _sidebar, self._sidebar_dots = build_sidebar(parent, self._nav_canvases, self._show_page, self._set_nav_hover)
        self._draw_sidebar_dots()

    def _show_page(self, page_key: str):
        self._active_page = page_key
        for key, frame in self._pages.items():
            action = frame.grid if key == page_key else frame.grid_remove
            action()
        refresh_sidebar(self._nav_canvases, page_key, self._hover_page)
        if page_key != "dashboard":
            title, subtitle = PAGE_TITLES[page_key]
            self._add_log(f"Opened {title.title()} page - {subtitle}", "info")

    def _set_nav_hover(self, page_key: str, active: bool):
        self._hover_page = page_key if active else None
        refresh_sidebar(self._nav_canvases, self._active_page, self._hover_page)

    def _draw_mini_orb(self, parent, size=32):
        canvas = ctk.CTkCanvas(parent, width=size, height=size, bg=BG, highlightthickness=0)
        draw_mini_orb(canvas, size, palette=PALETTE, phase=self._mini_orb_phase)
        return canvas

    def _draw_equalizer(self):
        draw_equalizer(self._equalizer, self._signal_phase, palette=PALETTE, activity=self._state_profile.signal_activity)
        self._signal_phase = (self._signal_phase + 0.18 * self._state_profile.reactor_speed) % (math.pi * 2)
        self.after(90, self._draw_equalizer)

    def _draw_waveform(self):
        draw_waveform(self._wave_canvas, self._signal_phase, palette=PALETTE, activity=self._state_profile.signal_activity)
        self.after(70, self._draw_waveform)

    def _draw_sidebar_dots(self):
        draw_sidebar_dots(self._sidebar_dots, self._sidebar_phase, palette=PALETTE)
        self._sidebar_phase = (self._sidebar_phase + 0.22) % (math.pi * 2)
        self.after(120, self._draw_sidebar_dots)

    def _draw_bottom_reactor(self):
        draw_mini_orb(self._bottom_orb, 58, palette=PALETTE, phase=self._mini_orb_phase)
        self._mini_orb_phase = (self._mini_orb_phase + 0.08) % (math.pi * 2)
        self.after(90, self._draw_bottom_reactor)

    def _draw_background(self, _event=None):
        self.after_idle(lambda: draw_background_depth(self._background, palette=PALETTE))

    def _mini_value(self, parent, label: str, value: str, color: str):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=8)
        ctk.CTkLabel(frame, text=label, font=font("mono", 8, "bold"), text_color=TEXT_DIM).pack(anchor="w")
        value_label = ctk.CTkLabel(frame, text=value, font=font("mono", 10, "bold"), text_color=color)
        value_label.pack(anchor="w")
        return value_label

    def _draw_hologram(self):
        self._ring_angle = draw_hologram_figure(
            self._canvas,
            self._ring_angle,
            accent=self._state_profile.accent,
            speed=self._state_profile.reactor_speed,
        )
        self.after(34, self._draw_hologram)

    def set_assistant_state(self, state: str, detail: str | None = None, *, log_event: bool = True):
        profile = get_state_profile(state)
        self._assistant_state = profile.name
        self._state_profile = profile
        subtitle = detail or profile.subtitle
        self._title_label.configure(text=profile.title, text_color=profile.accent)
        self._subtitle_label.configure(text=subtitle)
        self._status_label.configure(text=profile.status, text_color=profile.accent)
        if self._runtime_status_label is not None:
            self._runtime_status_label.configure(text=profile.name)
        if log_event:
            self._add_log(f"State changed to {profile.name}", "task")
    def _add_log(self, message: str, kind: str = "info"):
        event = normalize_log_event(message, kind)

        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"> {event.message}\n")
        end_idx = self._log_box.index("end-1c")
        line_num = int(end_idx.split(".")[0])
        self._log_box.tag_add(event.kind, f"{line_num - 1}.0", f"{line_num}.0")
        self._log_box.tag_config(event.kind, foreground=event.color)
        self._log_box.configure(state="disabled")
        self._log_box.see("end")

        content = self._log_box.get("1.0", "end").split("\n")
        if len(content) > 18:
            self._log_box.configure(state="normal")
            self._log_box.delete("1.0", "2.0")
            self._log_box.configure(state="disabled")

    def _update_ui(self, message: str):
        message = message.strip()
        if not message:
            return
        lowered = message.lower()
        clean_message = message.replace("JARVIS:", "JARVIS:").strip()
        inferred_state = infer_state_from_message(clean_message)
        if inferred_state:
            self.after(0, lambda: self.set_assistant_state(inferred_state, detail=clean_message, log_event=False))
        log_kind = infer_log_kind(clean_message)
        self.after(0, lambda: self._add_log(clean_message, log_kind))
        if "jarvis:" in lowered or "[cmd]" in lowered or "you:" in lowered:
            self.after(0, self._increment_command_count)
        if "jarvis:" in lowered:
            self.after(1800, lambda: self.set_assistant_state("STANDBY", log_event=False))
        elif "error" in lowered or "failed" in lowered:
            self.after(2400, lambda: self.set_assistant_state("STANDBY", log_event=False))
        elif inferred_state == "STANDBY":
            self.after(1200, lambda: self.set_assistant_state("STANDBY", log_event=False))

    def _increment_command_count(self):
        self._cmd_count += 1
        self._cmd_label.configure(text=str(self._cmd_count))

    def _start_updates(self):
        self._update_clock()
        self._update_metrics()

    def _update_clock(self):
        now = datetime.datetime.now()
        clock = now.strftime("%H:%M:%S")
        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        date_text = f"{days[now.weekday()]}  {now.day} {months[now.month - 1]} {now.year}"

        self._clock_label.configure(text=clock)
        self._date_label.configure(text=date_text)

        elapsed = int(time.time() - self._start_time)
        hours = str(elapsed // 3600).zfill(2)
        minutes = str((elapsed % 3600) // 60).zfill(2)
        seconds = str(elapsed % 60).zfill(2)
        self._uptime_label.configure(text=f"{hours}:{minutes}:{seconds}")

        self.after(1000, self._update_clock)

    def _update_metrics(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        self._cpu_label.configure(text=f"{cpu:.0f}%")
        self._ram_label.configure(text=f"{ram:.0f}%")

        cpu_color = RED if cpu > 80 else AMBER if cpu > 60 else BLUE
        ram_color = RED if ram > 85 else AMBER if ram > 70 else BLUE
        self._cpu_label.configure(text_color=cpu_color)
        self._ram_label.configure(text_color=ram_color)
        self._refresh_runtime_labels()
        refresh_info_pages(self._pages)

        self.after(2000, self._update_metrics)

    def _start_jarvis(self):
        if self._jarvis_started:
            return
        self._jarvis_started = True
        set_ui_callback(self._update_ui)
        thread = threading.Thread(target=start_jarvis, daemon=True)
        thread.start()

    def _start_onboarding_or_jarvis(self):
        def launch():
            self._start_jarvis()

        wizard = show_onboarding(self, on_complete=launch)
        if wizard is None:
            self._start_jarvis()

    def _refresh_runtime_labels(self):
        permission = get_active_permission_profile(os.environ)
        if "permission_profile" in self._runtime_value_labels:
            self._runtime_value_labels["permission_profile"].configure(text=permission["label"], text_color=AMBER if permission["id"] == "safe" else GREEN)
        ai_status = describe_ai_status(os.environ)
        if "ai_provider" in self._runtime_value_labels:
            self._runtime_value_labels["ai_provider"].configure(text=ai_status["provider"])
        runtime_report = build_slo_report()
        if self._runtime_status_label is not None:
            self._runtime_status_label.configure(
                text=runtime_report["status"].upper(),
                text_color=GREEN if runtime_report["status"] == "healthy" else AMBER if runtime_report["status"] == "watch" else RED,
            )
        if self._runtime_count_label is not None:
            self._runtime_count_label.configure(text=f"{runtime_report['events_seen']}")
        if self._runtime_latency_label is not None:
            latency = build_latency_snapshot()
            self._runtime_latency_label.configure(text=f"{latency['average_ms']}ms")

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _toggle_maximize(self):
        if self.state() == "zoomed":
            self.state("normal")
        else:
            self.state("zoomed")

def main() -> int:
    app = JarvisApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
