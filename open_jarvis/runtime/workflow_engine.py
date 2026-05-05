"""Simple workflow planner for multi-step Jarvis tasks."""

from __future__ import annotations


def build_workflow_plan(name: str, steps: list[str]) -> dict:
    """Turn user-supplied steps into an auditable workflow plan."""

    planned_steps = [
        {
            "order": index,
            "instruction": instruction,
            "status": "pending",
            "rollback": f"Mark step {index} as skipped and keep prior completed outputs.",
        }
        for index, instruction in enumerate(steps, start=1)
        if instruction.strip()
    ]
    return {
        "name": name,
        "status": "ready" if planned_steps else "empty",
        "steps": planned_steps,
        "next_step": planned_steps[0]["instruction"] if planned_steps else "",
    }
