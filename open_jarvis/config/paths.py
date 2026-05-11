"""Configuration path resolution with source and portable modes."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConfigPaths:
    config_dir: Path
    settings_file: Path
    portable: bool = False

    @classmethod
    def for_portable_root(cls, root: str | Path) -> ConfigPaths:
        base = Path(root)
        config_dir = base / "config"
        return cls(config_dir=config_dir, settings_file=config_dir / "settings.json", portable=True)


def _portable_root() -> Path | None:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        for candidate in (executable.parent, executable.parent.parent):
            if (candidate / "config").exists() or candidate.name == "Open.Jarvis":
                return candidate if candidate.name != "Open.Jarvis" else candidate.parent
    return None


def resolve_config_paths(
    *,
    env: Mapping[str, str] | None = None,
    config_path: str | Path | None = None,
    portable_root: str | Path | None = None,
) -> ConfigPaths:
    values = os.environ if env is None else env
    explicit = config_path or values.get("JARVIS_CONFIG_PATH")
    if explicit:
        settings = Path(explicit)
        return ConfigPaths(config_dir=settings.parent, settings_file=settings, portable=False)
    if portable_root is not None:
        return ConfigPaths.for_portable_root(portable_root)
    detected = _portable_root()
    if detected is not None:
        return ConfigPaths.for_portable_root(detected)
    base = Path(values.get("LOCALAPPDATA") or values.get("APPDATA") or Path.home() / "AppData" / "Local")
    config_dir = base / "Open.Jarvis"
    return ConfigPaths(config_dir=config_dir, settings_file=config_dir / "settings.json", portable=False)
