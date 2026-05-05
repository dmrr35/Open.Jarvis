"""COMMANDS - All JARVIS commands."""

from __future__ import annotations

from time import perf_counter

from open_jarvis.audio.ses_motoru import speak
from open_jarvis.commands.action_dispatcher import execute_action as dispatch_execute_action
from open_jarvis.commands.groq_router import analyze_with_groq, summarize_text
from open_jarvis.commands.local_intent_router import route_local_intent
from open_jarvis.health.observability import record_latency_metric
from open_jarvis.memory import add_to_short_term, detect_and_save_preference, track_command
from open_jarvis.runtime.ui_bridge import send_log, send_state
from open_jarvis.utils.jarvis_logging import get_logger

logger = get_logger("commands")


def execute_action(action):
    """Handles single or combo actions via the dispatcher."""

    context = {
        "speak": speak,
        "logger": logger,
        "summarize_text": summarize_text,
    }
    return dispatch_execute_action(action, context)


def process_command(command: str) -> bool:
    """Main command handler that sends to Groq and executes the result."""

    logger.info("Received command: %s", command)

    if any(k in command for k in ["goodbye jarvis", "shut down jarvis"]):
        speak("Farewell, sir. Jarvis shutting down.")
        return False

    add_to_short_term("user", command)
    track_command(command)

    pref_response = detect_and_save_preference(command)
    if pref_response:
        send_log("[SPEAKING] Speaking preference response")
        speak(pref_response)
        add_to_short_term("jarvis", pref_response)
        return True

    route_start = perf_counter()
    send_state("PROCESSING", "Routing command")
    local_action = route_local_intent(command)
    if local_action is not None:
        record_latency_metric("local_router", (perf_counter() - route_start) * 1000, command=command[:120], action=local_action.get("action"))
        logger.info("Routing command locally without Groq: %s", local_action.get("action"))
        send_log(f"[TASK] Routing locally: {local_action.get('action')}")
        action_start = perf_counter()
        send_state("EXECUTING", f"Running {local_action.get('action')}")
        send_log(f"[TASK] Executing action: {local_action.get('action')}")
        result = execute_action(local_action)
        record_latency_metric("action_dispatch", (perf_counter() - action_start) * 1000, command=command[:120], action=local_action.get("action"))
        logger.info("Local command completed with result=%s", result)
        send_log("[OK] Local command completed" if result else "[ERROR] Local command failed")
        send_state("STANDBY" if result else "ERROR", "Local command completed" if result else "Local command failed")
        return result

    logger.info("Routing command to Groq.")
    print("Analyzing with Groq...")
    send_state("PROCESSING", "Routing command to Groq")
    send_log("[TASK] Routing command to Groq")
    llm_start = perf_counter()
    action = analyze_with_groq(command)
    record_latency_metric("llm_router", (perf_counter() - llm_start) * 1000, command=command[:120], action=action.get("action", "multi"))

    response_text = action.get("response", "")
    if response_text:
        add_to_short_term("jarvis", response_text)

    action_start = perf_counter()
    send_state("EXECUTING", f"Running {action.get('action', 'multi')}")
    send_log(f"[TASK] Executing action: {action.get('action', 'multi')}")
    result = execute_action(action)
    record_latency_metric("action_dispatch", (perf_counter() - action_start) * 1000, command=command[:120], action=action.get("action", "multi"))
    logger.info("Command completed with result=%s", result)
    send_log("[OK] Command completed" if result else "[ERROR] Command failed")
    send_state("STANDBY" if result else "ERROR", "Command completed" if result else "Command failed")
    return result


komutu_isle = process_command
