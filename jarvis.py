"""
JARVIS - Main File
Run with UI:      python arayuz.py
Run in terminal:  python jarvis.py
"""

from jarvis_runtime import set_ui_callback, start_jarvis

__all__ = ["start_jarvis", "set_ui_callback"]


if __name__ == "__main__":
    start_jarvis()
