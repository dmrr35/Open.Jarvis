"""Assistant state profiles for the JARVIS cockpit UI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantStateProfile:
    """Visual and textual behavior for one assistant runtime state."""

    name: str
    title: str
    subtitle: str
    status: str
    accent: str
    reactor_speed: float
    signal_activity: float


ASSISTANT_STATE_ORDER = (
    "BOOTING",
    "STANDBY",
    "LISTENING",
    "PROCESSING",
    "EXECUTING",
    "SPEAKING",
    "ERROR",
    "OFFLINE",
)


ASSISTANT_STATE_PROFILES = {
    "BOOTING": AssistantStateProfile(
        name="BOOTING",
        title="J A R V I S",
        subtitle="Initializing assistant runtime...",
        status="BOOTING CORE",
        accent="#4CEBFF",
        reactor_speed=1.4,
        signal_activity=0.45,
    ),
    "STANDBY": AssistantStateProfile(
        name="STANDBY",
        title="J A R V I S",
        subtitle="I am a virtual assistant JARVIS, how may I help you?",
        status="STANDBY - SAY JARVIS",
        accent="#00D7FF",
        reactor_speed=1.0,
        signal_activity=0.35,
    ),
    "LISTENING": AssistantStateProfile(
        name="LISTENING",
        title="LISTENING",
        subtitle="Voice input active. Waiting for your command...",
        status="LISTENING...",
        accent="#4CEBFF",
        reactor_speed=1.65,
        signal_activity=1.0,
    ),
    "PROCESSING": AssistantStateProfile(
        name="PROCESSING",
        title="PROCESSING",
        subtitle="Analyzing request and selecting the best route...",
        status="PROCESSING REQUEST",
        accent="#89F2FF",
        reactor_speed=1.9,
        signal_activity=0.7,
    ),
    "EXECUTING": AssistantStateProfile(
        name="EXECUTING",
        title="EXECUTING",
        subtitle="Running the selected command...",
        status="EXECUTING COMMAND",
        accent="#00FFC6",
        reactor_speed=1.55,
        signal_activity=0.55,
    ),
    "SPEAKING": AssistantStateProfile(
        name="SPEAKING",
        title="RESPONDING",
        subtitle="Voice response active...",
        status="RESPONDING...",
        accent="#4CEBFF",
        reactor_speed=1.25,
        signal_activity=0.95,
    ),
    "ERROR": AssistantStateProfile(
        name="ERROR",
        title="ERROR",
        subtitle="Command failed. Check the command stream for details.",
        status="COMMAND FAILED",
        accent="#FF4D6D",
        reactor_speed=0.8,
        signal_activity=0.2,
    ),
    "OFFLINE": AssistantStateProfile(
        name="OFFLINE",
        title="OFFLINE",
        subtitle="Assistant services are unavailable.",
        status="OFFLINE",
        accent="#FFC857",
        reactor_speed=0.45,
        signal_activity=0.15,
    ),
}


def get_state_profile(state: str) -> AssistantStateProfile:
    """Return a known state profile, falling back to standby."""

    return ASSISTANT_STATE_PROFILES.get(state.upper(), ASSISTANT_STATE_PROFILES["STANDBY"])


def infer_state_from_message(message: str) -> str | None:
    """Infer a dashboard state from a runtime callback message."""

    lowered = message.lower()
    if "[state]" in lowered:
        for state in ASSISTANT_STATE_ORDER:
            if state.lower() in lowered:
                return state
    if "error" in lowered or "failed" in lowered:
        return "ERROR"
    if "[speaking]" in lowered or "speaking started" in lowered:
        return "SPEAKING"
    if "jarvis:" in lowered:
        return "SPEAKING"
    if "listening" in lowered or "wake word detected" in lowered:
        return "LISTENING"
    if "executing" in lowered or "launching" in lowered or "dispatch" in lowered:
        return "EXECUTING"
    if "analysis" in lowered or "processing" in lowered or "routing" in lowered or "you:" in lowered:
        return "PROCESSING"
    if "completed" in lowered or "success" in lowered or "[ok]" in lowered:
        return "STANDBY"
    return None
