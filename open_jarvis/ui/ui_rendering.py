"""Canvas rendering helpers for the JARVIS desktop UI."""

from __future__ import annotations

import math
import random


def draw_reactor_rings(canvas, angle: float, *, accent: str) -> float:
    """Draw the premium aurora core and return the next angle."""

    canvas.delete("all")
    width = int(canvas["width"])
    height = int(canvas["height"])
    cx, cy = width // 2, height // 2
    base = min(width, height) // 2 - 54
    radii = [base, int(base * 0.78), int(base * 0.57), int(base * 0.37)]
    colors = ["#182528", "#253238", "#3d6b63", "#79f2d0"]
    speeds = [0.45, -0.9, 1.35, -1.9]

    for offset, fill in [(0, "#071011"), (18, "#0a1516"), (36, "#0e1b1d")]:
        canvas.create_oval(cx - base + offset, cy - base + offset, cx + base - offset, cy + base - offset, fill=fill, outline="")

    for stripe in range(8):
        y = cy - base + stripe * (base * 2 / 7)
        wave = 18 * math.sin(math.radians(angle + stripe * 29))
        canvas.create_line(cx - base + 18, y, cx - 20 + wave, y - 18, cx + base - 18, y + 8, fill="#102124", width=1, smooth=True)

    for index, (radius, color, speed) in enumerate(zip(radii, colors, speeds, strict=True)):
        ring_angle = angle * speed
        x0, y0 = cx - radius, cy - radius
        x1, y1 = cx + radius, cy + radius
        dash = (18, 10) if index in {0, 2} else None
        canvas.create_oval(x0, y0, x1, y1, outline=color, width=2, dash=dash)

        arc_start = (ring_angle + index * 33) % 360
        canvas.create_arc(x0, y0, x1, y1, start=arc_start, extent=72 + index * 12, outline=accent, width=3, style="arc")

        dot_x = cx + radius * math.cos(math.radians(ring_angle))
        dot_y = cy + radius * math.sin(math.radians(ring_angle))
        canvas.create_oval(dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5, fill=accent, outline="")

    core = int(base * 0.31)
    canvas.create_rectangle(cx - core, cy - core, cx + core, cy + core, fill="#0a1011", outline="#f0b85a", width=2)
    canvas.create_line(cx - core, cy, cx + core, cy, fill="#253238", width=1)
    canvas.create_line(cx, cy - core, cx, cy + core, fill="#253238", width=1)
    canvas.create_text(cx, cy - 9, text="JARVIS", fill="#f4efe5", font=("Orbitron", 18, "bold"))
    canvas.create_text(cx, cy + 17, text="OBSIDIAN CORE", fill="#aab2aa", font=("Cascadia Mono", 8, "bold"))
    return (angle + 0.7) % 360


def build_hologram_layout(width: int, height: int, angle: float = 0) -> dict:
    """Return deterministic geometry for a circular cyber hologram HUD."""

    cx = width // 2
    cy = height // 2
    base = min(width, height) // 2 - 18
    rings = [base, int(base * 0.84), int(base * 0.68), int(base * 0.49), int(base * 0.31), int(base * 0.16)]
    arcs = []
    for index, radius in enumerate(rings[:-1]):
        for segment in range(3):
            start = (angle * (0.55 + index * 0.13) + segment * 120 + index * 19) % 360
            extent = 36 + (index % 3) * 12
            arcs.append({"radius": radius, "start": start, "extent": extent, "width": 3 if index < 2 else 2})

    spokes = []
    for spoke in range(24):
        degrees = math.radians(spoke * 15 + angle * 0.4)
        inner = rings[-2] if spoke % 2 else rings[-3]
        outer = rings[0] - (10 if spoke % 3 else 0)
        spokes.append(
            (
                cx + inner * math.cos(degrees),
                cy + inner * math.sin(degrees),
                cx + outer * math.cos(degrees),
                cy + outer * math.sin(degrees),
            )
        )

    randomizer = random.Random(int(angle * 10) + width + height)
    particles = []
    for _ in range(72):
        degrees = math.radians(randomizer.randint(0, 359))
        radius = randomizer.randint(rings[-2], rings[0] + 28)
        particles.append((cx + radius * math.cos(degrees), cy + radius * math.sin(degrees), randomizer.choice([1, 1, 2])))

    ticks = []
    for tick in range(72):
        degrees = math.radians(tick * 5)
        outer = rings[0] + 7
        inner = rings[0] - (8 if tick % 6 else 16)
        ticks.append(
            (
                cx + inner * math.cos(degrees),
                cy + inner * math.sin(degrees),
                cx + outer * math.cos(degrees),
                cy + outer * math.sin(degrees),
            )
        )

    reactor_triads = []
    inner_radius = rings[-3]
    outer_radius = rings[-2]
    for segment in range(12):
        center_angle = math.radians(segment * 30 + angle * 0.22)
        left_angle = center_angle - math.radians(7)
        right_angle = center_angle + math.radians(7)
        reactor_triads.append(
            (
                cx + inner_radius * math.cos(left_angle),
                cy + inner_radius * math.sin(left_angle),
                cx + outer_radius * math.cos(center_angle),
                cy + outer_radius * math.sin(center_angle),
                cx + inner_radius * math.cos(right_angle),
                cy + inner_radius * math.sin(right_angle),
            )
        )

    light_channels = []
    channel_inner = rings[-2] + 8
    channel_outer = rings[1] - 14
    for channel in range(8):
        degrees = math.radians(channel * 45 - angle * 0.35)
        light_channels.append(
            (
                cx + channel_inner * math.cos(degrees),
                cy + channel_inner * math.sin(degrees),
                cx + channel_outer * math.cos(degrees),
                cy + channel_outer * math.sin(degrees),
            )
        )

    label_offset = 30
    labels = {
        "top": (cx, max(4, cy - rings[0] - label_offset), "ARC REACTOR"),
        "left": (max(12, cx - rings[0] - label_offset), cy, "STABLE"),
        "right": (min(width - 12, cx + rings[0] + label_offset), cy, "ONLINE"),
        "bottom": (cx, min(height - 4, cy + rings[0] + label_offset), "JARVIS CORE"),
    }

    return {
        "center": (cx, cy),
        "rings": rings,
        "arcs": arcs,
        "spokes": spokes,
        "ticks": ticks,
        "reactor_triads": reactor_triads,
        "light_channels": light_channels,
        "labels": labels,
        "particles": particles,
    }


def draw_hologram_figure(canvas, angle: float, *, accent: str, speed: float = 1.0) -> float:
    """Draw a cyan circular hologram HUD inspired by cinematic JARVIS UIs."""

    canvas.delete("all")
    width = int(canvas["width"])
    height = int(canvas["height"])
    layout = build_hologram_layout(width, height, angle)
    dark_cyan = "#014a5a"
    mid_cyan = "#057b96"

    cx, cy = layout["center"]
    for y in range(22, height, 26):
        canvas.create_line(width * 0.16, y, width * 0.84, y + 5 * math.sin(math.radians(angle + y)), fill="#021418", width=1)

    base = layout["rings"][0]
    for glow, color in [(34, "#00141a"), (24, "#001f29"), (14, "#022b36")]:
        canvas.create_oval(cx - base - glow, cy - base - glow, cx + base + glow, cy + base + glow, outline=color, width=1)

    halo_radius = layout["rings"][1] + 5
    for start, extent in [(28, 74), (146, 72), (266, 58)]:
        animated_start = (start - angle * 0.45) % 360
        for width_boost, color in [(10, "#00384f"), (6, "#087fa3"), (3, "#8DEEFF")]:
            canvas.create_arc(
                cx - halo_radius,
                cy - halo_radius,
                cx + halo_radius,
                cy + halo_radius,
                start=animated_start,
                extent=extent,
                outline=color,
                width=width_boost,
                style="arc",
            )

    for index, radius in enumerate(layout["rings"]):
        color = accent if index in {1, 4} else mid_cyan if index % 2 == 0 else dark_cyan
        dash = (14, 9) if index in {0, 2} else (5, 7) if index == 3 else None
        canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=color, width=2 if index < 2 else 1, dash=dash)

    for index, tick in enumerate(layout["ticks"]):
        canvas.create_line(*tick, fill=accent if index % 6 == 0 else dark_cyan, width=2 if index % 6 == 0 else 1)

    for index, spoke in enumerate(layout["spokes"]):
        canvas.create_line(*spoke, fill=mid_cyan if index % 4 == 0 else "#03313b", width=1)

    for index, channel in enumerate(layout["light_channels"]):
        canvas.create_line(*channel, fill=accent if index % 2 == 0 else mid_cyan, width=3 if index % 2 == 0 else 2)

    for index, triad in enumerate(layout["reactor_triads"]):
        canvas.create_polygon(
            triad,
            outline=accent if index % 3 == 0 else mid_cyan,
            fill="#001219" if index % 2 == 0 else "",
            width=1,
        )

    for index, arc in enumerate(layout["arcs"]):
        radius = arc["radius"]
        color = accent if index % 4 in {0, 1} else mid_cyan
        canvas.create_arc(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            start=arc["start"],
            extent=arc["extent"],
            outline=color,
            width=arc["width"],
            style="arc",
        )

    for x, y, size in layout["particles"]:
        color = accent if size == 2 else mid_cyan
        canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline="")

    pulse = 28 + int(7 * math.sin(math.radians(angle * 2)))
    canvas.create_oval(cx - pulse - 12, cy - pulse - 12, cx + pulse + 12, cy + pulse + 12, outline="#003f52", width=2)
    canvas.create_oval(cx - pulse, cy - pulse, cx + pulse, cy + pulse, outline=accent, width=3)
    canvas.create_oval(cx - 13, cy - 13, cx + 13, cy + 13, outline=mid_cyan, width=2)
    canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=accent, outline="")
    canvas.create_text(cx, cy, text="J", fill=accent, font=("Orbitron", 18, "bold"))
    for anchor, (label_x, label_y, text) in layout["labels"].items():
        text_anchor = "center"
        if anchor == "left":
            text_anchor = "e"
        elif anchor == "right":
            text_anchor = "w"
        canvas.create_text(label_x, label_y, text=text, fill=mid_cyan, font=("Cascadia Mono", 9, "bold"), anchor=text_anchor)
    return (angle + 1.2 * speed) % 360
