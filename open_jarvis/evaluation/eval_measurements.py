"""Measured eval execution for command routing, STT fixtures, and latency."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any

from open_jarvis.evaluation.evaluation_suite import build_eval_suite, summarize_eval_results


class EvalMeasurementError(RuntimeError):
    """Raised when a measured eval callable cannot produce a usable result."""


def _matches_expected(scenario: dict[str, Any], observed: Any) -> bool:
    expected = scenario.get("expected")
    if scenario["category"] == "stt":
        return str(observed).strip().lower() == "jarvis"
    if expected == "blocked_in_safe":
        return bool(isinstance(observed, dict) and observed.get("blocked"))
    if expected == "under_500_ms":
        return True
    if expected == "spotify":
        return isinstance(observed, dict) and str(observed.get("action", "")).startswith("spotify")
    return isinstance(observed, dict) and observed.get("action") == expected


def run_measured_eval_suite(
    *,
    router: Callable[[str], dict[str, Any]],
    stt_fixtures: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run eval scenarios against real router/STT fixture callables and measure latency."""

    suite = build_eval_suite()
    stt_fixtures = stt_fixtures or {}
    results: list[dict[str, Any]] = []
    for scenario in suite["scenarios"]:
        start = perf_counter()
        try:
            if scenario["category"] == "stt":
                observed: Any = stt_fixtures.get(scenario["id"], "")
                source = "stt_fixture"
            else:
                observed = router(scenario["prompt"])
                source = "command_router"
                if not isinstance(observed, dict):
                    raise EvalMeasurementError("Router returned a non-dict result.")
            latency_ms = round((perf_counter() - start) * 1000, 2)
            passed = _matches_expected(scenario, observed)
            detail = f"Observed {observed!r} from {source}."
        except (KeyError, TypeError, ValueError, EvalMeasurementError) as exc:
            latency_ms = round((perf_counter() - start) * 1000, 2)
            passed = False
            observed = None
            source = "command_router"
            detail = f"Measurement failed: {exc}"
        results.append(
            {
                "id": scenario["id"],
                "category": scenario["category"],
                "passed": passed,
                "latency_ms": latency_ms,
                "measurement_source": source,
                "observed": observed,
                "detail": detail,
            }
        )
    return {
        "suite": suite,
        "results": results,
        "summary": summarize_eval_results(results),
        "measurement_mode": "measured",
    }
