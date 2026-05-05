"""Premium visual design tokens for the JARVIS desktop UI."""

from __future__ import annotations

PALETTE = {
    "bg": "#070A12",
    "bg_elevated": "#0C1322",
    "surface": "#0C1322",
    "surface_soft": "#101B2D",
    "surface_glass": "#061018",
    "line": "#11304A",
    "line_soft": "#1A4564",
    "line_hot": "#00D7FF",
    "cyan": "#00D7FF",
    "cyan_soft": "#4CEBFF",
    "cyan_hot": "#89F2FF",
    "blue": "#0aa7d8",
    "amber": "#FFC857",
    "green": "#00FFC6",
    "red": "#FF4D6D",
    "text": "#D8F6FF",
    "text_muted": "#8FB7C8",
    "text_faint": "#5F7D8E",
    "ink": "#061018",
}

FONTS = {
    "display": "Orbitron",
    "ui": "Bahnschrift",
    "mono": "Cascadia Mono",
}

RADIUS = {
    "card": 8,
    "button": 8,
    "pill": 999,
}


def build_design_tokens() -> dict:
    """Return stable design tokens for tests, docs, and UI modules."""

    return {
        "name": "Cyber Hologram",
        "palette": dict(PALETTE),
        "fonts": dict(FONTS),
        "radius": dict(RADIUS),
        "spacing": {"xs": 6, "sm": 10, "md": 16, "lg": 24, "xl": 34},
    }


def font(kind: str, size: int, weight: str | None = None) -> tuple:
    """Build a CustomTkinter font tuple from theme tokens."""

    family = FONTS.get(kind, FONTS["ui"])
    return (family, size, weight) if weight else (family, size)
