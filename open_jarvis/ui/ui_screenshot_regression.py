"""Screenshot regression checks for the JARVIS desktop cockpit."""

from __future__ import annotations

import time
from pathlib import Path

from PIL import Image, ImageGrab

PAGES_TO_CAPTURE = ("dashboard", "system", "integrations", "security")
MIN_CYAN_PIXELS = 900
MIN_BRIGHT_PIXELS = 1800


def _capture_window(app, output: Path) -> dict:
    for _ in range(10):
        app.update()
        app.update_idletasks()
        time.sleep(0.08)
    box = (app.winfo_rootx(), app.winfo_rooty(), app.winfo_rootx() + app.winfo_width(), app.winfo_rooty() + app.winfo_height())
    image = ImageGrab.grab(box)
    output.parent.mkdir(exist_ok=True)
    image.save(output)
    return analyze_image(output)


def analyze_image(path: str | Path) -> dict:
    """Return visual health metrics for a captured cockpit screenshot."""

    image = Image.open(path).convert("RGB")
    pixel_access = image.load()
    pixels = [pixel_access[x, y] for y in range(image.height) for x in range(image.width)]
    cyan_pixels = sum(1 for r, g, b in pixels if g > 130 and b > 150 and r < 80)
    bright_pixels = sum(1 for r, g, b in pixels if r + g + b > 180)
    dark_pixels = sum(1 for r, g, b in pixels if r + g + b < 45)
    return {
        "path": str(path),
        "width": image.width,
        "height": image.height,
        "cyan_pixels": cyan_pixels,
        "bright_pixels": bright_pixels,
        "dark_pixels": dark_pixels,
    }


def validate_metrics(metrics: dict) -> tuple[bool, list[str]]:
    """Validate screenshot metrics against stable HUD health thresholds."""

    failures = []
    if metrics["width"] < 1200 or metrics["height"] < 700:
        failures.append("screenshot resolution is too small")
    if metrics["cyan_pixels"] < MIN_CYAN_PIXELS:
        failures.append("cyan HUD signal is too weak")
    if metrics["bright_pixels"] < MIN_BRIGHT_PIXELS:
        failures.append("visible UI content is too sparse")
    if metrics["dark_pixels"] < metrics["bright_pixels"]:
        failures.append("dark cockpit background is not dominant")
    return not failures, failures


def run_screenshot_regression(output_dir: str | Path = "exports") -> dict:
    """Capture key pages and verify they are nonblank HUD screens."""

    from open_jarvis.ui.arayuz import JarvisApp

    class ScreenshotJarvisApp(JarvisApp):
        def _start_onboarding_or_jarvis(self):
            return None

    output_dir = Path(output_dir)
    app = ScreenshotJarvisApp()
    results = []
    try:
        app.geometry("1600x900+0+0")
        app.attributes("-topmost", True)
        app.lift()
        app.focus_force()
        for page in PAGES_TO_CAPTURE:
            app._show_page(page)
            metrics = _capture_window(app, output_dir / f"ui-regression-{page}.png")
            ok, failures = validate_metrics(metrics)
            results.append({"page": page, "ok": ok, "failures": failures, **metrics})
    finally:
        app.destroy()
    return {
        "status": "ok" if all(result["ok"] for result in results) else "failed",
        "results": results,
    }


def main() -> int:
    report = run_screenshot_regression()
    print(f"UI screenshot regression: {report['status']}")
    for result in report["results"]:
        print(
            f"{result['page']}: {result['width']}x{result['height']} "
            f"cyan={result['cyan_pixels']} bright={result['bright_pixels']} "
            f"failures={','.join(result['failures']) or 'none'}"
        )
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
