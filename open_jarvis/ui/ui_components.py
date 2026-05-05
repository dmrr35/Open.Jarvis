"""Reusable CustomTkinter components for the JARVIS UI."""

from __future__ import annotations

import customtkinter as ctk

from open_jarvis.ui.ui_theme import PALETTE, RADIUS, font


def section_label(parent, title: str, subtitle: str | None = None):
    """Create a consistent section heading block."""

    ctk.CTkLabel(parent, text=title, font=font("display", 18, "bold"), text_color=PALETTE["text"]).pack(pady=(26, 2), anchor="w", padx=22)
    if subtitle:
        ctk.CTkLabel(parent, text=subtitle, font=font("ui", 11), text_color=PALETTE["text_muted"]).pack(anchor="w", padx=22, pady=(0, 16))


def status_dot(parent, color: str | None = None, size: int = 8):
    """Create a small live-status dot."""

    return ctk.CTkLabel(parent, text="", fg_color=color or PALETTE["green"], width=size, height=size, corner_radius=999)


def metric_card(parent, title: str, *, pad: dict | None = None):
    """Create a metric card with label and progress bar."""

    frame = ctk.CTkFrame(
        parent,
        fg_color=PALETTE["surface"],
        corner_radius=RADIUS["card"],
        border_width=1,
        border_color=PALETTE["line"],
    )
    frame.pack(fill="x", **(pad or {"padx": 18, "pady": 8}))
    ctk.CTkLabel(frame, text=title, font=font("mono", 10, "bold"), text_color=PALETTE["text_muted"]).pack(anchor="w", padx=16, pady=(14, 0))
    label = ctk.CTkLabel(frame, text="--%", font=font("display", 31, "bold"), text_color=PALETTE["cyan"])
    label.pack(anchor="w", padx=16)
    bar = ctk.CTkProgressBar(frame, height=8, fg_color=PALETTE["bg"], progress_color=PALETTE["cyan"])
    bar.pack(fill="x", padx=16, pady=(8, 16))
    bar.set(0)
    return label, bar


def info_row(parent, label: str, value: str, color: str):
    """Create a compact label/value information row."""

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=20, pady=5)
    ctk.CTkLabel(frame, text=label, font=font("mono", 9, "bold"), text_color=PALETTE["text_muted"]).pack(anchor="w")
    value_label = ctk.CTkLabel(frame, text=value, font=font("display", 14, "bold"), text_color=color)
    value_label.pack(anchor="w")
    return value_label


def cockpit_button(parent, text: str, command):
    """Create a premium cockpit action button."""

    return ctk.CTkButton(
        parent,
        text=text,
        fg_color=PALETTE["surface_soft"],
        hover_color=PALETTE["blue"],
        font=font("ui", 12, "bold"),
        height=36,
        corner_radius=18,
        command=command,
    )
