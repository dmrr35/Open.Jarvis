"""Sidebar navigation helpers for the JARVIS cockpit UI."""

from __future__ import annotations

import customtkinter as ctk

from ui_hud_effects import draw_sidebar_nav_icon
from ui_theme import PALETTE

SIDEBAR_NAV_ITEMS = [
    ("dashboard", "core"),
    ("system", "pulse"),
    ("modules", "cube"),
    ("integrations", "nodes"),
    ("security", "shield"),
    ("settings", "gear"),
]


def build_sidebar(parent, nav_canvases: dict, on_select, on_hover) -> tuple[ctk.CTkFrame, ctk.CTkCanvas]:
    """Build the clickable sidebar and return the dot matrix canvas."""

    sidebar = ctk.CTkFrame(parent, fg_color="#07101C", corner_radius=0, width=90, border_width=1, border_color=PALETTE["line"])
    sidebar.grid(row=0, column=0, sticky="ns")
    sidebar.grid_propagate(False)
    for index, (page_key, icon) in enumerate(SIDEBAR_NAV_ITEMS):
        size = 60 if index == 0 else 46
        canvas = ctk.CTkCanvas(sidebar, width=size, height=size, bg="#07101C", highlightthickness=0)
        canvas.pack(pady=(30, 34) if index == 0 else 15)
        canvas.bind("<Button-1>", lambda _event, key=page_key: on_select(key))
        canvas.bind("<Enter>", lambda _event, key=page_key: on_hover(key, True))
        canvas.bind("<Leave>", lambda _event, key=page_key: on_hover(key, False))
        nav_canvases[page_key] = (canvas, icon)
    dots = ctk.CTkCanvas(sidebar, width=46, height=62, bg="#07101C", highlightthickness=0)
    dots.pack(side="bottom", pady=30)
    return sidebar, dots


def refresh_sidebar(nav_canvases: dict, active_page: str, hover_page: str | None = None) -> None:
    """Redraw sidebar icons with the active page highlighted."""

    for key, (canvas, icon) in nav_canvases.items():
        draw_sidebar_nav_icon(canvas, icon, palette=PALETTE, active=key == active_page, hover=key == hover_page)
