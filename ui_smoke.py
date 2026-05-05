"""Smoke helpers for validating the desktop UI without starting Jarvis runtime."""

from __future__ import annotations


def run_ui_smoke() -> dict:
    """Instantiate the main window, build widgets, and close it immediately."""

    from arayuz import JarvisApp

    class SmokeJarvisApp(JarvisApp):
        def _start_onboarding_or_jarvis(self):
            return None

        def _draw_rings(self):
            return None

    app = SmokeJarvisApp()
    try:
        app.update_idletasks()
        return {
            "status": "ok",
            "title": app.title(),
            "geometry": app.geometry(),
            "widgets": len(app.winfo_children()),
        }
    finally:
        app.destroy()


def main() -> int:
    result = run_ui_smoke()
    print(f"UI smoke: {result['status']}")
    print(f"Window title: {result['title']}")
    print(f"Top-level widgets: {result['widgets']}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
