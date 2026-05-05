"""Safe maintenance recommendations for logs, cache and memory."""

from __future__ import annotations


def build_maintenance_plan(metrics: dict) -> dict:
    """Return non-destructive maintenance actions sorted by value."""

    actions = []
    if int(metrics.get("memory_score", 100)) < 60:
        actions.append(
            {
                "id": "prune_memory",
                "title": "Prune memory",
                "safe": True,
                "command": 'python -c "from memory_store import prune_memory; prune_memory()"',
            }
        )
    if int(metrics.get("log_bytes", 0)) > 1_000_000:
        actions.append({"id": "rotate_logs", "title": "Rotate logs", "safe": True, "command": "python kontrol.py --no-pause"})
    if int(metrics.get("cache_bytes", 0)) > 1_000_000:
        actions.append({"id": "trim_cache", "title": "Trim cache", "safe": True, "command": "python -m compileall ."})
    return {"actions": actions, "count": len(actions)}
