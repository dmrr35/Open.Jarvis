"""Centralized process execution helpers."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence


def _validate_command(command: Sequence[str]) -> list[str]:
    if isinstance(command, str):
        raise TypeError("command must be a sequence of arguments, not a shell string")
    return [str(part) for part in command]


def launch_process(command: Sequence[str]):
    """Launch a process without invoking a shell."""

    return subprocess.Popen(_validate_command(command), shell=False)


def run_command(command: Sequence[str]):
    """Run a command with shell disabled."""

    return subprocess.run(_validate_command(command), check=False, shell=False)
