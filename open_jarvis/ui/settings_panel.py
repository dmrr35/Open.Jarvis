"""Headless-safe settings panel model plus a minimal CustomTkinter surface."""

from __future__ import annotations

from typing import Any

from open_jarvis.config.manager import ConfigManager
from open_jarvis.config.schema import FIELD_DEFINITIONS

CATEGORY_LABELS = {
    "general": "General",
    "ai": "AI Provider",
    "voice": "Voice",
    "runtime": "Runtime",
    "plugins": "Plugins",
    "spotify": "Spotify",
    "privacy": "Privacy",
}


def build_settings_view_model(config: dict[str, dict[str, Any]], secret_status: dict[str, str] | None = None) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {label: [] for label in CATEGORY_LABELS.values()}
    for key, field_def in FIELD_DEFINITIONS.items():
        category = field_def.category
        label = CATEGORY_LABELS.get(category, category.title())
        groups.setdefault(label, []).append(
            {
                "key": key,
                "label": field_def.name.replace("_", " ").title(),
                "value": config.get(category, {}).get(field_def.name, field_def.default),
                "type": field_def.value_type,
                "allowed_values": list(field_def.allowed_values),
                "editable": True,
                "restart_required": field_def.restart_required,
            }
        )
    groups["Secrets"] = [
        {"key": key, "label": key, "value": status, "type": "status", "editable": False}
        for key, status in sorted((secret_status or {}).items())
    ]
    return {"groups": {key: value for key, value in groups.items() if value}}


def collect_editable_settings(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {row["key"]: row.get("value", "") for row in rows if row.get("editable")}


class SettingsPanelModel:
    def __init__(self, manager: ConfigManager | None = None) -> None:
        self.manager = manager or ConfigManager()
        self.config = self.manager.load()

    def view_model(self) -> dict[str, Any]:
        return build_settings_view_model(self.config, self.manager.diagnostics().get("secret_status", {}))

    def save(self, updates: dict[str, Any]) -> dict[str, Any]:
        self.manager.set_many(updates)
        result = self.manager.validate()
        if not result.valid:
            return {"status": "error", "errors": result.errors, "warnings": result.warnings}
        self.manager.save(result.normalized)
        self.config = self.manager.load()
        return {"status": "saved", "warnings": result.warnings, "path": str(self.manager.paths.settings_file)}

    def reset(self) -> dict[str, Any]:
        self.config = self.manager.reset()
        return {"status": "reset", "config": self.config}
