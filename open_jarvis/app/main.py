"""Application entrypoint for Open J.A.R.V.I.S."""

from __future__ import annotations

import argparse

from open_jarvis.runtime.jarvis_runtime import set_ui_callback, start_jarvis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Open J.A.R.V.I.S terminal assistant.")
    parser.add_argument("--version", action="store_true", help="print the package version and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print("Open J.A.R.V.I.S 0.2.0")
        return 0
    start_jarvis()
    return 0


__all__ = ["build_parser", "main", "set_ui_callback", "start_jarvis"]


if __name__ == "__main__":
    raise SystemExit(main())
