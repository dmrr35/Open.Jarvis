import sys

sys.dont_write_bytecode = True

from open_jarvis.release.repo_hygiene import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
