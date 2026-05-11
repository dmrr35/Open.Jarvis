"""Runtime bridge for resolved configuration without broad env rewrites."""

from __future__ import annotations

from collections.abc import Mapping

from open_jarvis.config.manager import ConfigManager


def load_runtime_config(env: Mapping[str, str] | None = None) -> dict:
    manager = ConfigManager(env=env)
    config = manager.load()
    return {"config": config, "env": manager.as_env_mapping(), "diagnostics": manager.diagnostics()}


def resolved_env(env: Mapping[str, str] | None = None) -> dict[str, str]:
    return load_runtime_config(env=env)["env"]
