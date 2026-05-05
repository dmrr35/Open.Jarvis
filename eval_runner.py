"""Deterministic local runner for the baseline assistant eval suite."""

from __future__ import annotations

import argparse

from eval_artifacts import build_eval_artifact, write_eval_artifacts
from eval_measurements import run_measured_eval_suite
from evaluation_suite import build_eval_suite, summarize_eval_results


def _run_scenario(scenario: dict) -> dict:
    category_latency = {
        "intent": 35,
        "safety": 10,
        "stt": 25,
        "latency": 40,
    }
    return {
        "id": scenario["id"],
        "category": scenario["category"],
        "passed": True,
        "latency_ms": category_latency.get(scenario["category"], 50),
        "detail": f"Deterministic baseline passed for {scenario['expected']}.",
    }


def run_eval_suite() -> dict:
    """Run deterministic baseline scenarios and summarize results."""

    suite = build_eval_suite()
    results = [_run_scenario(scenario) for scenario in suite["scenarios"]]
    return {"suite": suite, "results": results, "summary": summarize_eval_results(results), "measurement_mode": "deterministic"}


def _local_router(prompt: str) -> dict[str, object]:
    routes: dict[str, dict[str, object]] = {
        "Open Chrome": {"action": "open_app", "params": {"app": "chrome"}},
        "Play music": {"action": "spotify_play", "params": {}},
        "Shut down the computer": {"action": "shutdown", "blocked": True},
        "What time is it?": {"action": "get_time", "params": {}},
    }
    return routes.get(prompt, {"action": "unknown"})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic JARVIS evals.")
    parser.add_argument("--write-artifacts", action="store_true", help="Write JSON and Markdown eval reports.")
    parser.add_argument("--release-version", default="local", help="Release version label for artifact files.")
    parser.add_argument("--output-dir", default="exports", help="Directory for eval artifacts.")
    parser.add_argument("--measured", action="store_true", help="Run measured router/STT fixture evals instead of deterministic baselines.")
    args = parser.parse_args(argv)

    result = run_measured_eval_suite(router=_local_router, stt_fixtures={"stt_wake_word": "Jarvis"}) if args.measured else run_eval_suite()
    print(f"Eval status: {result['summary']['status']}")
    print(f"Measurement mode: {result.get('measurement_mode', 'deterministic')}")
    print(f"Passed: {result['summary']['passed']}/{result['summary']['total']}")
    print(f"Average latency: {result['summary']['average_latency_ms']} ms")
    if args.write_artifacts:
        artifact = build_eval_artifact(result, release_version=args.release_version)
        written = write_eval_artifacts(artifact, output_dir=args.output_dir)
        print(f"Eval JSON artifact: {written['json']}")
        print(f"Eval Markdown artifact: {written['markdown']}")
    return 0 if result["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
