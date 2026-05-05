"""Eval artifact generation for release quality reports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_eval_artifact(eval_result: dict[str, Any], release_version: str = "local") -> dict[str, Any]:
    """Wrap eval results with release metadata for CI artifacts."""

    return {
        "report_type": "jarvis_eval_artifact",
        "release_version": release_version,
        "generated_at": datetime.now(UTC).isoformat(),
        "measurement_mode": eval_result.get("measurement_mode", "deterministic"),
        "summary": dict(eval_result.get("summary", {})),
        "suite": dict(eval_result.get("suite", {})),
        "results": list(eval_result.get("results", [])),
    }


def render_eval_markdown(artifact: dict[str, Any]) -> str:
    """Render a compact Markdown eval report."""

    summary = artifact.get("summary", {})
    lines = [
        "# Eval Artifact Report",
        "",
        f"- Release version: `{artifact.get('release_version', 'local')}`",
        f"- Measurement mode: `{artifact.get('measurement_mode', 'deterministic')}`",
        f"- Status: `{summary.get('status', 'unknown')}`",
        f"- Passed: `{summary.get('passed', 0)}/{summary.get('total', 0)}`",
        f"- Average latency: `{summary.get('average_latency_ms', 0)} ms`",
        "",
        "| Scenario | Category | Result | Latency ms |",
        "|---|---|---|---:|",
    ]
    for result in artifact.get("results", []):
        status = "pass" if result.get("passed") else "fail"
        lines.append(f"| {result.get('id', '')} | {result.get('category', '')} | {status} | {result.get('latency_ms', 0)} |")
    return "\n".join(lines) + "\n"


def write_eval_artifacts(artifact: dict[str, Any], output_dir: Path | str = "exports") -> dict[str, str]:
    """Write JSON and Markdown eval artifacts and return their paths."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    version = str(artifact.get("release_version", "local")).replace("/", "-")
    json_path = target / f"eval-artifact-{version}.json"
    markdown_path = target / f"eval-artifact-{version}.md"

    json_path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(render_eval_markdown(artifact), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}


def compare_eval_artifacts(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    latency_regression_ms: int = 25,
) -> dict[str, Any]:
    """Compare two eval artifacts and report release-quality regressions."""

    previous_summary = previous.get("summary", {})
    current_summary = current.get("summary", {})
    passed_delta = int(current_summary.get("passed", 0)) - int(previous_summary.get("passed", 0))
    latency_delta = float(current_summary.get("average_latency_ms", 0)) - float(previous_summary.get("average_latency_ms", 0))

    previous_results = {item.get("id"): item for item in previous.get("results", [])}
    regressions = []
    for result in current.get("results", []):
        scenario_id = result.get("id")
        old = previous_results.get(scenario_id, {})
        if old.get("passed") and not result.get("passed"):
            regressions.append({"id": scenario_id, "type": "pass_to_fail"})
        old_latency = float(old.get("latency_ms", 0))
        new_latency = float(result.get("latency_ms", 0))
        if old_latency and new_latency - old_latency > latency_regression_ms:
            regressions.append(
                {
                    "id": scenario_id,
                    "type": "latency",
                    "delta_ms": round(new_latency - old_latency, 1),
                }
            )

    if passed_delta < 0 and not any(item["type"] == "pass_count" for item in regressions):
        regressions.append({"id": "summary", "type": "pass_count", "delta": passed_delta})
    if latency_delta > latency_regression_ms:
        regressions.append({"id": "summary", "type": "average_latency", "delta_ms": round(latency_delta, 1)})

    return {
        "status": "regressed" if regressions else "stable",
        "passed_delta": passed_delta,
        "average_latency_delta_ms": round(latency_delta, 1),
        "regressions": regressions,
    }
