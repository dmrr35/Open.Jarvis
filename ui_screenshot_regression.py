import sys

sys.dont_write_bytecode = True

from open_jarvis.ui.ui_screenshot_regression import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
