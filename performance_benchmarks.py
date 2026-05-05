"""Small performance-budget helpers for local and CI checks."""

from __future__ import annotations


def build_performance_budget() -> dict[str, int]:
    """Return default performance budgets in milliseconds."""

    return {
        "startup": 1500,
        "command_route": 500,
        "health_check": 2000,
        "memory_load": 100,
        "eval_suite": 500,
    }


def summarize_benchmark_results(results: list[dict], budget: dict[str, int] | None = None) -> dict:
    """Compare benchmark results with budgets and report pass/fail counts."""

    budget = budget or build_performance_budget()
    enriched = []
    for result in results:
        test_id = str(result["id"])
        duration = int(result["duration_ms"])
        limit = int(budget.get(test_id, 1000))
        enriched.append({**result, "budget_ms": limit, "passed": duration <= limit})
    failed = sum(1 for item in enriched if not item["passed"])
    return {
        "status": "pass" if failed == 0 else "fail",
        "total": len(enriched),
        "failed": failed,
        "passed": len(enriched) - failed,
        "results": enriched,
    }
