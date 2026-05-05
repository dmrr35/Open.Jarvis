"""Route parsed actions into domain-specific handlers."""

from __future__ import annotations

import os
import time
from typing import Any

from open_jarvis.commands.action_schema import validate_action_payload
from open_jarvis.commands.domains.media_actions import handle_media_action
from open_jarvis.commands.domains.memory_actions import handle_memory_action
from open_jarvis.commands.domains.runtime_actions import handle_runtime_action

DomainContext = dict[str, Any]

DOMAIN_HANDLERS = (
    handle_runtime_action,
    handle_media_action,
    handle_memory_action,
)


def action_sequence_delay() -> float:
    """Return the delay between multi-action steps."""

    try:
        return max(0.0, float(os.getenv("JARVIS_ACTION_SEQUENCE_DELAY", "0.1")))
    except ValueError:
        return 0.1


def execute_single_action(action: str, params: dict, context: DomainContext) -> bool:
    """Execute one action by delegating to the domain handlers."""

    for handler in DOMAIN_HANDLERS:
        result = handler(action, params, context)
        if result is not None:
            return bool(result)

    logger = context.get("logger")
    if logger is not None:
        logger.warning("Unhandled action: %s", action)
    return True


def execute_action(action: dict, context: DomainContext) -> bool:
    """Execute a single or multi-action payload."""

    speak = context["speak"]
    validation = validate_action_payload(action)
    if not validation.valid:
        logger = context.get("logger")
        if logger is not None:
            logger.warning("Invalid action payload: %s", validation.reason)
        speak(f"Invalid action payload, sir. Reason: {validation.reason}.")
        return False

    if "actions" in action:
        response = action.get("response", "")
        if response:
            speak(response)
        for sub_action in action["actions"]:
            if not isinstance(sub_action, dict) or not sub_action.get("action"):
                logger = context.get("logger")
                if logger is not None:
                    logger.warning("Malformed sub-action payload: %s", sub_action)
                speak("I skipped a malformed action, sir. Reason: it did not include an action name.")
                return False
            result = execute_single_action(
                sub_action["action"],
                sub_action.get("params", {}),
                context,
            )
            if result is False:
                return False
            delay = action_sequence_delay()
            if delay:
                time.sleep(delay)
        return True

    response = action.get("response", "")
    if response:
        speak(response)
    return execute_single_action(action.get("action", "talk"), action.get("params", {}), context)
