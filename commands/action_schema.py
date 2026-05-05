"""Validation helpers for model and local-router action payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionValidationResult:
    valid: bool
    reason: str = ""


def _invalid(reason: str) -> ActionValidationResult:
    return ActionValidationResult(False, reason)


def _validate_params(payload: dict[str, Any], label: str) -> ActionValidationResult:
    params = payload.get("params", {})
    if not isinstance(params, dict):
        return _invalid(f"{label} params must be an object")
    return ActionValidationResult(True)


def validate_action_payload(payload: Any) -> ActionValidationResult:
    """Validate the common action envelope before dispatch."""

    if not isinstance(payload, dict):
        return _invalid("action payload must be an object")

    if "actions" in payload:
        actions = payload.get("actions")
        if not isinstance(actions, list) or not actions:
            return _invalid("actions must be a non-empty list")
        for index, sub_action in enumerate(actions):
            if not isinstance(sub_action, dict):
                return _invalid(f"actions[{index}] must be an object")
            params_result = _validate_params(sub_action, f"actions[{index}]")
            if not params_result.valid:
                return params_result
        return ActionValidationResult(True)

    action = payload.get("action")
    if not isinstance(action, str) or not action.strip():
        return _invalid("action payload must include an action name")

    params_result = _validate_params(payload, "action")
    if not params_result.valid:
        return params_result

    response = payload.get("response", "")
    if not isinstance(response, str):
        return _invalid("response must be a string")

    return ActionValidationResult(True)


__all__ = ["ActionValidationResult", "validate_action_payload"]
