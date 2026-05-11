"""Validation and normalization for Open.Jarvis configuration."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from open_jarvis.config.defaults import build_default_config
from open_jarvis.config.schema import FIELD_DEFINITIONS, FieldDefinition
from open_jarvis.config.sensitive import reject_sensitive_payload

TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
FALSE_VALUES = {"0", "false", "no", "off", "disabled"}


@dataclass
class ValidationResult:
    valid: bool
    normalized: dict[str, dict[str, Any]]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)


def parse_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return default


def _coerce_value(field_def: FieldDefinition, value: Any) -> tuple[Any, str | None]:
    default = copy.deepcopy(field_def.default)
    if value is None:
        return default, f"{field_def.key} is empty; using default."
    if field_def.value_type == "bool":
        coerced = parse_bool(value, default)
        if not isinstance(value, bool) and str(value).strip().lower() not in TRUE_VALUES | FALSE_VALUES:
            return coerced, f"{field_def.key} has invalid boolean value; using default."
        return coerced, None
    if field_def.value_type in {"string", "path"}:
        coerced = str(value).strip()
        if field_def.key == "voice.wake_word":
            coerced = " ".join(coerced.lower().split())
            if not coerced:
                return default, f"{field_def.key} must not be empty; using default."
        if field_def.allowed_values and coerced.lower() not in field_def.allowed_values:
            return default, f"{field_def.key} must be one of {', '.join(field_def.allowed_values)}; using default."
        return coerced.lower() if field_def.allowed_values else coerced, None
    if field_def.value_type == "int":
        try:
            coerced = int(value)
        except (TypeError, ValueError):
            return default, f"{field_def.key} must be an integer; using default."
        return _range_checked(field_def, coerced, default)
    if field_def.value_type == "float":
        try:
            coerced = float(value)
        except (TypeError, ValueError):
            return default, f"{field_def.key} must be a number; using default."
        return _range_checked(field_def, coerced, default)
    return value, None


def _range_checked(field_def: FieldDefinition, value: int | float, default: Any) -> tuple[Any, str | None]:
    if field_def.minimum is not None and value < field_def.minimum:
        return default, f"{field_def.key} is below minimum {field_def.minimum}; using default."
    if field_def.maximum is not None and value > field_def.maximum:
        return default, f"{field_def.key} is above maximum {field_def.maximum}; using default."
    return value, None


def validate_config(data: Mapping[str, Any] | None) -> ValidationResult:
    payload = data or {}
    normalized = build_default_config()
    errors = reject_sensitive_payload(payload)
    warnings: list[str] = []
    unknown: list[str] = []

    for category, values in payload.items():
        if not isinstance(values, Mapping):
            warnings.append(f"{category} must be an object; using defaults.")
            continue
        for name, value in values.items():
            key = f"{category}.{name}"
            field_def = FIELD_DEFINITIONS.get(key)
            if field_def is None:
                if not errors or not any(key in error for error in errors):
                    unknown.append(key)
                    warnings.append(f"Unknown setting {key} was ignored.")
                continue
            coerced, warning = _coerce_value(field_def, value)
            normalized[category][name] = coerced
            if warning:
                warnings.append(warning)

    return ValidationResult(valid=not errors, normalized=normalized, errors=errors, warnings=warnings, unknown_fields=unknown)
