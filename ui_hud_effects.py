"""Premium HUD canvas effects for the JARVIS desktop UI."""

from __future__ import annotations

import math

import customtkinter as ctk


def draw_background_depth(canvas, *, palette: dict) -> None:
    """Draw subtle glow, scanlines, and HUD depth behind the main stage."""

    canvas.delete("all")
    width = int(canvas["width"] or canvas.winfo_width() or 1400)
    height = int(canvas["height"] or canvas.winfo_height() or 760)
    bg = palette["bg"]
    accent = palette["cyan"]
    line = palette["line"]
    soft = palette["line_soft"]

    canvas.create_rectangle(0, 0, width, height, fill=bg, outline="")
    cx = int(width * 0.60)
    cy = int(height * 0.31)
    for radius, color in [(360, "#071725"), (300, "#082033"), (240, "#092a3f"), (180, "#073247")]:
        canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=color, width=1)
    for y in range(14, height, 28):
        canvas.create_line(0, y, width, y, fill="#081322", width=1)
    for y in range(0, height, 5):
        canvas.create_line(0, y, width, y, fill="#070d17", width=1)
    for index in range(36):
        x = (index * 137) % max(width, 1)
        y = (index * 89) % max(height, 1)
        canvas.create_rectangle(x, y, x + 1, y + 1, fill=soft if index % 4 == 0 else line, outline="")
    for side in range(5):
        alpha_color = ["#060912", "#060b14", "#070d17", "#07101b", "#07121e"][side]
        canvas.create_rectangle(side, side, width - side, side + 1, fill=alpha_color, outline="")
        canvas.create_rectangle(side, height - side - 2, width - side, height - side - 1, fill=alpha_color, outline="")
    canvas.create_line(width * 0.18, height * 0.04, width * 0.82, height * 0.04, fill=line, width=1)
    canvas.create_line(width * 0.22, height * 0.78, width * 0.78, height * 0.78, fill=line, width=1)
    canvas.create_line(width * 0.42, height * 0.04, width * 0.58, height * 0.04, fill=accent, width=1)


def add_terminal_corners(parent, *, accent: str) -> None:
    """Place compact HUD corner accents on a terminal frame."""

    for x, y, sx, sy in [(0, 0, 1, 1), (1, 0, -1, 1), (0, 1, 1, -1), (1, 1, -1, -1)]:
        corner = ctk.CTkFrame(parent, fg_color="transparent", width=24, height=16)
        corner.place(relx=x, rely=y, x=0 if sx > 0 else -24, y=0 if sy > 0 else -16)
        ctk.CTkFrame(corner, fg_color=accent, width=20, height=2).place(x=0 if sx > 0 else 4, y=0 if sy > 0 else 14)
        ctk.CTkFrame(corner, fg_color=accent, width=2, height=14).place(x=0 if sx > 0 else 22, y=0 if sy > 0 else 2)


def draw_active_sidebar_icon(canvas, *, palette: dict) -> None:
    """Draw the active sidebar reactor icon with a restrained outer glow."""

    accent = palette["cyan"]
    glow = palette["cyan_soft"]
    panel = palette["surface"]
    canvas.delete("all")
    canvas.create_rectangle(2, 2, 58, 58, outline="#123c58", width=3)
    canvas.create_rectangle(6, 6, 54, 54, fill=panel, outline=accent, width=1)
    canvas.create_oval(16, 16, 44, 44, outline="#085e79", width=5)
    canvas.create_oval(18, 18, 42, 42, outline=accent, width=3)
    canvas.create_oval(25, 25, 35, 35, outline=glow, width=1)


def draw_sidebar_icon(canvas, icon: str, *, palette: dict, clear: bool = True) -> None:
    """Draw compact line icons matching the reference HUD sidebar."""

    accent = palette["cyan"]
    if clear:
        canvas.delete("all")
    if icon == "pulse":
        canvas.create_line(7, 24, 17, 24, 21, 13, 26, 33, 30, 24, 39, 24, fill=accent, width=2)
    elif icon == "cube":
        canvas.create_polygon(23, 8, 35, 15, 35, 30, 23, 38, 11, 30, 11, 15, outline=accent, fill="", width=1)
        canvas.create_line(23, 8, 23, 23, fill=accent)
        canvas.create_line(35, 15, 23, 23, 11, 15, fill=accent)
        canvas.create_line(23, 23, 23, 38, fill=accent)
    elif icon == "nodes":
        for line in [(23, 13, 13, 31), (23, 13, 33, 31), (15, 34, 31, 34)]:
            canvas.create_line(*line, fill=accent, width=1)
        for x, y in [(23, 9), (11, 34), (35, 34)]:
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, outline=accent, width=1)
    elif icon == "shield":
        canvas.create_polygon(23, 8, 34, 14, 32, 29, 23, 38, 14, 29, 12, 14, outline=accent, fill="", width=2)
        canvas.create_line(23, 13, 23, 33, fill=accent, width=1)
    else:
        canvas.create_oval(17, 17, 29, 29, outline=accent, width=2)
        for angle in range(0, 360, 45):
            x1 = 23 + 8 * math.cos(math.radians(angle))
            y1 = 23 + 8 * math.sin(math.radians(angle))
            x2 = 23 + 15 * math.cos(math.radians(angle))
            y2 = 23 + 15 * math.sin(math.radians(angle))
            canvas.create_line(x1, y1, x2, y2, fill=accent, width=2)


def draw_sidebar_nav_icon(canvas, icon: str, *, palette: dict, active: bool = False, hover: bool = False) -> None:
    """Draw one clickable sidebar navigation icon."""

    canvas.delete("all")
    if active or hover:
        outer = palette["cyan_soft"] if hover else "#123c58"
        inner = palette["cyan_hot"] if hover else palette["cyan"]
        canvas.create_rectangle(2, 2, int(canvas["width"]) - 2, int(canvas["height"]) - 2, outline=outer, width=3)
        canvas.create_rectangle(6, 6, int(canvas["width"]) - 6, int(canvas["height"]) - 6, fill=palette["surface"], outline=inner, width=1)
    if icon == "core":
        accent = palette["cyan"]
        offset = 7 if active else 0
        canvas.create_oval(13 + offset, 13 + offset, 33 + offset, 33 + offset, outline=accent, width=2)
        canvas.create_oval(19 + offset, 19 + offset, 27 + offset, 27 + offset, outline=palette["cyan_soft"], width=1)
        return
    draw_sidebar_icon(canvas, icon, palette=palette, clear=False)


def draw_sidebar_dots(canvas, phase: float, *, palette: dict) -> None:
    """Draw a subtle pulsing dot matrix in the lower sidebar."""

    accent = palette["cyan"]
    glow = palette["cyan_soft"]
    canvas.delete("all")
    for row in range(3):
        for col in range(3):
            pulse = (math.sin(phase + row * 0.6 + col * 0.4) + 1) / 2
            color = glow if pulse > 0.72 else accent
            size = 2 + pulse
            x = 10 + col * 13
            y = 12 + row * 13
            canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline="")


def draw_mini_orb(canvas, size: int, *, palette: dict, phase: float = 0.0) -> None:
    """Draw a small animated reactor/radar detail."""

    canvas.delete("all")
    center = size // 2
    accent = palette["cyan"]
    glow = palette["cyan_soft"]
    line = palette["line"]
    pulse = 2 * math.sin(phase)
    canvas.create_oval(3, 3, size - 3, size - 3, outline=line, width=1)
    canvas.create_oval(8, 8, size - 8, size - 8, outline="#06374d", width=1)
    canvas.create_oval(center - 8 - pulse, center - 8 - pulse, center + 8 + pulse, center + 8 + pulse, outline=accent, width=2)
    canvas.create_oval(center - 3, center - 3, center + 3, center + 3, fill=glow, outline="")
    for angle in [phase * 30, phase * 30 + 90, phase * 30 + 180, phase * 30 + 270]:
        x1 = center + (center - 9) * math.cos(math.radians(angle))
        y1 = center + (center - 9) * math.sin(math.radians(angle))
        x2 = center + (center - 2) * math.cos(math.radians(angle))
        y2 = center + (center - 2) * math.sin(math.radians(angle))
        canvas.create_line(x1, y1, x2, y2, fill=accent, width=1)


def draw_equalizer(canvas, phase: float, *, palette: dict, activity: float = 1.0) -> None:
    """Draw a natural audio spectrum with controlled glow."""

    canvas.delete("all")
    accent = palette["cyan"]
    glow = palette["cyan_soft"]
    for index in range(18):
        center_weight = 1 - min(abs(index - 9) / 9, 1)
        wave = math.sin(phase + index * 0.72)
        secondary = math.sin(phase * 1.7 + index * 0.31)
        value = 6 + int((center_weight * 36 + (wave + 1) * 8 + (secondary + 1) * 4) * activity)
        x = 8 + index * 10
        color = glow if center_weight > 0.75 else accent
        canvas.create_rectangle(x - 1, 64 - value - 2, x + 4, 64, fill="#05364a", outline="")
        canvas.create_rectangle(x, 64 - value, x + 3, 64, fill=color, outline="")


def draw_waveform(canvas, phase: float, *, palette: dict, activity: float = 1.0) -> None:
    """Draw the bottom telemetry waveform with grid and glow."""

    canvas.delete("all")
    width = int(canvas["width"])
    height = int(canvas["height"])
    for x in range(16, width, 24):
        canvas.create_line(x, 5, x, height - 5, fill="#0b2234", width=1)
    for y in range(12, height, 12):
        canvas.create_line(5, y, width - 5, y, fill="#0b2234", width=1)
    points = []
    baseline = height // 2
    for index in range(36):
        x = 8 + index * ((width - 16) / 35)
        carrier = math.sin(phase * 1.4 + index * 0.8)
        detail = math.sin(phase * 2.2 + index * 1.9)
        envelope = 0.45 + 0.55 * math.sin(phase * 0.6 + index * 0.16) ** 2
        y = baseline + (carrier * 7 + detail * 3) * envelope * activity
        points.extend([x, y])
    canvas.create_line(points, fill="#074b67", width=4, smooth=True)
    canvas.create_line(points, fill=palette["cyan"], width=1, smooth=True)
    for index in range(0, len(points), 8):
        canvas.create_oval(points[index] - 1, points[index + 1] - 1, points[index] + 1, points[index + 1] + 1, fill=palette["cyan"], outline="")
