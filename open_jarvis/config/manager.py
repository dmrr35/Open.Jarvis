"""Central configuration manager for non-secret Open.Jarvis settings."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import threading
from collections.abc import Mapping
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from open_jarvis.config.defaults import build_default_config
from open_jarvis.config.paths import ConfigPaths, resolve_config_paths
from open_jarvis.config.schema import ENV_TO_FIELD, FIELD_DEFINITIONS
from open_jarvis.config.sensitive import build_sensitive_status, is_sensitive_key, reject_sensitive_payload
from open_jarvis.config.validation import ValidationResult, validate_config


class ConfigManager:
    def __init__(self, *, paths: ConfigPaths | None = None, env: Mapping[str, str] | None = None) -> None:
        self.paths = paths or resolve_config_paths(env=env)
        self.env = dict(os.environ if env is None else env)
        self._config = build_default_config()
        self._diagnostics: dict[str, Any] = {}
        self._lock = threading.RLock()

    def load(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            self._diagnostics = {
                "config_path": str(self.paths.settings_file),
                "config_exists": self.paths.settings_file.exists(),
                "portable": self.paths.portable,
                "warnings": [],
                "conflicts": [],
                "env_overrides": [],
            }
            merged = build_default_config()
            self._merge_env(merged)
            file_payload = self._read_file_payload()
            if file_payload:
                self._merge_user_settings(merged, file_payload)
            result = validate_config(merged)
            self._config = result.normalized
            self._diagnostics["warnings"].extend(result.warnings)
            if result.errors:
                self._diagnostics["warnings"].extend(result.errors)
            self._diagnostics["secret_status"] = build_sensitive_status(self.env)
            return copy.deepcopy(self._config)

    def save(self, config: Mapping[str, Any] | None = None) -> Path:
        with self._lock:
            candidate = copy.deepcopy(config if config is not None else self._config)
            secret_errors = reject_sensitive_payload(candidate)
            if secret_errors:
                raise ValueError("; ".join(secret_errors))
            result = validate_config(candidate)
            if not result.valid:
                raise ValueError("; ".join(result.errors))
            self.paths.config_dir.mkdir(parents=True, exist_ok=True)
            payload = {"schema_version": 1, "settings": result.normalized}
            handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.paths.config_dir, delete=False, prefix="settings-", suffix=".tmp")
            temp_path = Path(handle.name)
            try:
                with handle:
                    json.dump(payload, handle, indent=2, sort_keys=True)
                    handle.write("\n")
                temp_path.replace(self.paths.settings_file)
            except OSError:
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                raise
            self._config = result.normalized
            self._diagnostics["config_exists"] = True
            return self.paths.settings_file

    def reset(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            self._config = build_default_config()
            return copy.deepcopy(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        category, _, name = key.partition(".")
        if not name:
            return default
        return copy.deepcopy(self._config.get(category, {}).get(name, default))

    def set(self, key: str, value: Any) -> None:
        if is_sensitive_key(key):
            raise ValueError(f"Sensitive setting {key} is environment-only and cannot be stored in settings.json.")
        category, _, name = key.partition(".")
        if not name:
            raise KeyError(key)
        self._config.setdefault(category, {})[name] = value

    def set_many(self, values: Mapping[str, Any]) -> None:
        for key, value in values.items():
            self.set(key, value)

    def validate(self, config: Mapping[str, Any] | None = None) -> ValidationResult:
        return validate_config(config or self._config)

    def diagnostics(self) -> dict[str, Any]:
        data = copy.deepcopy(self._diagnostics)
        data.setdefault("config_path", str(self.paths.settings_file))
        data.setdefault("config_exists", self.paths.settings_file.exists())
        data.setdefault("portable", self.paths.portable)
        data.setdefault("warnings", [])
        data.setdefault("conflicts", [])
        data.setdefault("secret_status", build_sensitive_status(self.env))
        return data

    def export_safe(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "settings": copy.deepcopy(self._config),
            "diagnostics": self.diagnostics(),
            "secrets": build_sensitive_status(self.env),
        }

    def as_env_mapping(self) -> dict[str, str]:
        values = dict(self.env)
        for key, field_def in FIELD_DEFINITIONS.items():
            if not field_def.env_var:
                continue
            value = self.get(key, field_def.default)
            values[field_def.env_var] = _env_value(field_def.env_var, value)
        return values

    def get_secret_status(self, name: str) -> str:
        return build_sensitive_status(self.env, keys=(name,))[name]

    def _merge_env(self, target: dict[str, dict[str, Any]]) -> None:
        env_payload: dict[str, dict[str, Any]] = {}
        for env_var, key in ENV_TO_FIELD.items():
            if env_var not in self.env:
                continue
            field_def = FIELD_DEFINITIONS[key]
            env_payload.setdefault(field_def.category, {})[field_def.name] = self.env[env_var]
            self._diagnostics["env_overrides"].append(env_var)
        result = validate_config(env_payload)
        self._diagnostics["warnings"].extend(result.warnings)
        for category, values in result.normalized.items():
            for name, value in values.items():
                key = f"{category}.{name}"
                field_def = FIELD_DEFINITIONS.get(key)
                if field_def and field_def.env_var in self.env:
                    target[category][name] = value

    def _read_file_payload(self) -> dict[str, Any]:
        path = self.paths.settings_file
        if not path.exists():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, JSONDecodeError) as exc:
            self._diagnostics["load_error"] = str(exc)
            return {}
        if not isinstance(raw, Mapping):
            self._diagnostics["warnings"].append("settings.json must contain an object; using defaults.")
            return {}
        settings = raw.get("settings", raw)
        return dict(settings) if isinstance(settings, Mapping) else {}

    def _merge_user_settings(self, target: dict[str, dict[str, Any]], payload: Mapping[str, Any]) -> None:
        sanitized = copy.deepcopy(dict(payload))
        for error in reject_sensitive_payload(sanitized):
            self._diagnostics["warnings"].append(error)
        sanitized = _drop_secret_keys(sanitized)
        result = validate_config(sanitized)
        self._diagnostics["warnings"].extend(result.warnings)
        for category, values in result.normalized.items():
            for name, value in values.items():
                key = f"{category}.{name}"
                field_def = FIELD_DEFINITIONS.get(key)
                if field_def is None:
                    continue
                if category in sanitized and isinstance(sanitized[category], Mapping) and name in sanitized[category]:
                    if field_def.env_var in self.env:
                        self._diagnostics["conflicts"].append(f"{field_def.env_var} overridden by user setting {key}.")
                    target[category][name] = value


def _drop_secret_keys(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if is_sensitive_key(str(key)):
            continue
        if isinstance(value, Mapping):
            nested = _drop_secret_keys(dict(value))
            cleaned[key] = nested
        else:
            cleaned[key] = value
    return cleaned


def _env_value(env_var: str, value: Any) -> str:
    if isinstance(value, bool):
        if env_var == "JARVIS_OFFLINE_STT":
            return "1" if value else "0"
        return "true" if value else "false"
    return str(value)
