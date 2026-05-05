"""E2E desktop test readiness planning."""

from __future__ import annotations

FLOW_DESCRIPTIONS = {
    "ui_start": "UI opens and renders the main Jarvis shell.",
    "voice_command": "Wake word and command listener can route a command.",
    "onboarding": "First-run setup shows pass/fail setup steps.",
    "permission_profile": "Risky actions respect the active permission profile.",
    "health_center": "Health output is grouped by severity and fix hints.",
}


def build_e2e_readiness_plan(flows: list[str] | None = None) -> dict:
    """Build a checklist for manual or automated desktop E2E coverage."""

    requested = flows or list(FLOW_DESCRIPTIONS)
    planned = [
        {
            "id": flow,
            "description": FLOW_DESCRIPTIONS.get(flow, "Custom user journey."),
            "status": "planned",
        }
        for flow in requested
    ]
    return {
        "status": "ready" if planned else "empty",
        "coverage_target": "desktop-critical",
        "flows": planned,
    }
