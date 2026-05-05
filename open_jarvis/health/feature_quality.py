"""Feature quality catalog for product readiness tracking."""

from __future__ import annotations

from typing import Any

FEATURES: tuple[dict[str, Any], ...] = (
    {
        "id": "onboarding",
        "name": "Onboarding wizard",
        "category": "setup",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "pure status checks, no network calls",
        "performance_budget_ms": 5,
        "security": "never prints secret values",
        "quality_score": 95,
        "next_improvement": "Add live credential connectivity probes behind explicit user action.",
    },
    {
        "id": "permission_profiles",
        "name": "Permission profiles",
        "category": "safety",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py", "tests/test_runtime_safety.py"],
        "performance": "constant-time profile lookup",
        "performance_budget_ms": 1,
        "security": "blocks destructive actions outside admin mode",
        "quality_score": 96,
        "next_improvement": "Add per-profile safety rules for trusted and strict modes.",
    },
    {
        "id": "memory_panel",
        "name": "Memory panel",
        "category": "memory",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "copy-on-write updates keep caller state safe",
        "performance_budget_ms": 10,
        "security": "privacy mode can stop writes before persistence",
        "quality_score": 94,
        "next_improvement": "Add bulk edit and restore operations.",
    },
    {
        "id": "command_history",
        "name": "Command history and undo",
        "category": "runtime",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "bounded deque prevents unbounded growth",
        "performance_budget_ms": 2,
        "security": "undo requires an explicit registered callback",
        "quality_score": 95,
        "next_improvement": "Persist safe command history summaries between sessions.",
    },
    {
        "id": "plugin_marketplace",
        "name": "Plugin marketplace",
        "category": "plugins",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py", "tests/test_runtime_helpers.py"],
        "performance": "local manifest scan only",
        "performance_budget_ms": 50,
        "security": "validates signer, verifies signatures, and blocks path traversal entrypoints",
        "quality_score": 94,
        "next_improvement": "Add remote marketplace indexing with signed catalog metadata.",
    },
    {
        "id": "llm_fallback",
        "name": "LLM fallback",
        "category": "ai",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "provider selection is local and deterministic",
        "performance_budget_ms": 1,
        "security": "does not call external providers during selection",
        "quality_score": 94,
        "next_improvement": "Add local endpoint health probe with timeout.",
    },
    {
        "id": "workflow_mode",
        "name": "Workflow mode",
        "category": "automation",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "linear plan construction",
        "performance_budget_ms": 5,
        "security": "plans are descriptive until executed by guarded action handlers",
        "quality_score": 92,
        "next_improvement": "Add resumable workflow state persistence.",
    },
    {
        "id": "health_center",
        "name": "Health center",
        "category": "diagnostics",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py", "tests/test_health_cli.py"],
        "performance": "sorts a small in-memory check list",
        "performance_budget_ms": 10,
        "security": "fix commands are explicit; memory pruning and log rotation are allowlisted and recorded as masked runtime audit events",
        "quality_score": 94,
        "next_improvement": "Add setup validation repair coverage.",
    },
    {
        "id": "maintenance",
        "name": "Maintenance mode",
        "category": "operations",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "recommendation-only until user runs a command",
        "performance_budget_ms": 5,
        "security": "marks recommended cleanup actions as safe-only",
        "quality_score": 93,
        "next_improvement": "Add dry-run output with expected freed space.",
    },
    {
        "id": "privacy_mode",
        "name": "Privacy mode",
        "category": "privacy",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py", "tests/test_action_dispatcher.py"],
        "performance": "simple runtime flag checks",
        "performance_budget_ms": 1,
        "security": "masks secrets before runtime event logs and disables memory writes when enabled",
        "quality_score": 96,
        "next_improvement": "Extend masking policy to future external exporters.",
    },
    {
        "id": "release_panel",
        "name": "Release readiness",
        "category": "release",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py", "tests/test_runtime_helpers.py"],
        "performance": "local policy validation only",
        "performance_budget_ms": 5,
        "security": "requires signing key length and trusted signers",
        "quality_score": 94,
        "next_improvement": "Add CI artifact signature verification report.",
    },
    {
        "id": "plugin_runner",
        "name": "Real plugin sandbox",
        "category": "plugins",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "copies trusted plugins to short-lived workspaces and captures bounded subprocess output",
        "performance_budget_ms": 10,
        "security": "blocks path traversal, requires valid signatures, runs in scoped temp workspaces, applies timeout and resource policy",
        "quality_score": 95,
        "next_improvement": "Add deeper OS-level network isolation for third-party plugins.",
    },
    {
        "id": "offline_profile",
        "name": "Offline profile",
        "category": "offline",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "pure environment capability analysis",
        "performance_budget_ms": 5,
        "security": "keeps local/offline capability decisions explicit",
        "quality_score": 93,
        "next_improvement": "Add guided installers for Vosk, Piper, and local LLM providers.",
    },
    {
        "id": "evaluation_suite",
        "name": "Assistant eval suite",
        "category": "quality",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "scenario metadata and summary calculation stay local and fast",
        "performance_budget_ms": 5,
        "security": "includes safety scenarios as a required release category",
        "quality_score": 94,
        "next_improvement": "Add richer production prompt fixtures and negative safety cases.",
    },
    {
        "id": "eval_runner",
        "name": "Measured eval runner",
        "category": "quality",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "measures local command-router and STT fixture latency without network calls",
        "performance_budget_ms": 10,
        "security": "keeps release-gate safety scenarios mandatory and records observed routing decisions",
        "quality_score": 96,
        "next_improvement": "Connect measured evals to full voice pipeline fixtures.",
    },
    {
        "id": "release_build",
        "name": "Windows release artifact pipeline",
        "category": "release",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py", "tests/test_project_quality_files.py"],
        "performance": "streaming SHA256 avoids loading large artifacts into memory",
        "performance_budget_ms": 5,
        "security": "computes SHA256, signs release payloads, verifies signatures, and writes CI artifacts",
        "quality_score": 95,
        "next_improvement": "Add installer notarization and downloadable release notes.",
    },
    {
        "id": "model_installer",
        "name": "Signed model installer plan",
        "category": "offline",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "static install plan construction with signed catalog lookup",
        "performance_budget_ms": 5,
        "security": "uses signed checksum catalogs, official manual download URLs, and explicit env setup",
        "quality_score": 95,
        "next_improvement": "Add guided downloads that verify catalog checksums before extraction.",
    },
    {
        "id": "plugin_marketplace_ui",
        "name": "Plugin marketplace UI",
        "category": "plugins",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "local manifest rendering only",
        "performance_budget_ms": 25,
        "security": "surfaces blocked plugin issues, sandbox readiness, and explicit approval actions before execution",
        "quality_score": 94,
        "next_improvement": "Wire approval buttons to signed state changes from the dialog.",
    },
    {
        "id": "voice_calibration",
        "name": "Voice calibration",
        "category": "voice",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "pure sample analysis with no microphone dependency",
        "performance_budget_ms": 5,
        "security": "only recommends local threshold values and does not record audio",
        "quality_score": 94,
        "next_improvement": "Wire the recommendation into the onboarding wizard with live microphone sampling.",
    },
    {
        "id": "performance_benchmarks",
        "name": "Performance benchmarks",
        "category": "quality",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "static budget comparison for CI-friendly checks",
        "performance_budget_ms": 5,
        "security": "does not execute untrusted commands or external network calls",
        "quality_score": 93,
        "next_improvement": "Collect real startup, routing, and health-check timings in CI artifacts.",
    },
    {
        "id": "plugin_signature_verification",
        "name": "Plugin signature verification",
        "category": "plugins",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "HMAC verification over deterministic manifest JSON",
        "performance_budget_ms": 5,
        "security": "rejects unsigned, unknown-signer, and tampered manifests before enablement",
        "quality_score": 95,
        "next_improvement": "Move from shared HMAC keys to asymmetric public-key signatures for third-party plugins.",
    },
    {
        "id": "plugin_enable_state",
        "name": "Plugin enable/disable state",
        "category": "plugins",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "small JSON state file with direct plugin-name lookup",
        "performance_budget_ms": 5,
        "security": "only enables plugins after signature verification succeeds",
        "quality_score": 94,
        "next_improvement": "Add UI buttons with explicit approval copy and state-change audit events.",
    },
    {
        "id": "eval_artifacts",
        "name": "Measured eval artifact reports",
        "category": "quality",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "writes compact JSON and Markdown reports with measurement-mode evidence",
        "performance_budget_ms": 10,
        "security": "keeps safety scenario outcomes and observed measurement sources visible in release artifacts",
        "quality_score": 95,
        "next_improvement": "Compare measured CI artifacts against previous release baselines automatically.",
    },
    {
        "id": "model_checksum_verification",
        "name": "Signed offline model catalog",
        "category": "offline",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "single SHA256 pass over archives plus deterministic catalog signature verification",
        "performance_budget_ms": 100,
        "security": "detects missing archives, tampered archives, untrusted catalogs, and catalog signature mismatch",
        "quality_score": 95,
        "next_improvement": "Move release catalogs to asymmetric signatures for public distribution.",
    },
    {
        "id": "eval_artifact_comparison",
        "name": "Eval artifact comparison",
        "category": "quality",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "linear comparison over scenario result rows",
        "performance_budget_ms": 10,
        "security": "keeps safety pass-to-fail regressions visible before release",
        "quality_score": 95,
        "next_improvement": "Persist previous release artifact lookup in CI.",
    },
    {
        "id": "plugin_approval_audit",
        "name": "Plugin approval audit trail",
        "category": "plugins",
        "quality": "production-ready core",
        "tests": ["tests/test_product_features.py"],
        "performance": "append-only JSON state audit for enable and disable events",
        "performance_budget_ms": 5,
        "security": "records who approved plugin state changes and why",
        "quality_score": 94,
        "next_improvement": "Add signed audit events and UI approval prompts.",
    },
    {
        "id": "ui_design_system",
        "name": "Cyber Hologram UI design system",
        "category": "ux",
        "quality": "production-ready core",
        "tests": ["tests/test_project_quality_files.py", "ui_screenshot_regression.py"],
        "performance": "static design tokens, reusable components, and screenshot regression checks shared by UI modules",
        "performance_budget_ms": 1,
        "security": "keeps public UI text English and avoids secret rendering",
        "quality_score": 95,
        "next_improvement": "Add pixel-diff baselines after the cockpit layout stabilizes.",
    },
)


def build_feature_catalog() -> list[dict[str, Any]]:
    """Return a copy of the feature catalog for docs, UI, or health views."""

    return [dict(feature) for feature in FEATURES]


def build_feature_quality_report() -> dict[str, Any]:
    """Summarize feature readiness and highlight weak spots."""

    features = build_feature_catalog()
    weak = [
        feature
        for feature in features
        if not feature.get("tests")
        or "prototype" in feature.get("quality", "")
        or int(feature.get("quality_score", 0)) < 90
        or int(feature.get("performance_budget_ms", 0)) <= 0
    ]
    average_score = round(sum(int(feature["quality_score"]) for feature in features) / len(features), 1) if features else 0
    return {
        "total": len(features),
        "production_ready": len(features) - len(weak),
        "average_score": average_score,
        "weak": weak,
        "features": features,
    }


def render_feature_quality_report() -> str:
    """Render a compact CLI report for feature readiness."""

    report = build_feature_quality_report()
    lines = [
        "Feature Quality Report",
        f"Total features: {report['total']}",
        f"Production-ready core: {report['production_ready']}",
        f"Average score: {report['average_score']}",
        "",
        "| Feature | Score | Budget ms | Next improvement |",
        "|---|---:|---:|---|",
    ]
    for feature in report["features"]:
        lines.append(
            f"| {feature['id']} | {feature['quality_score']} | {feature['performance_budget_ms']} | {feature['next_improvement']} |"
        )
    if report["weak"]:
        lines.extend(["", "Weak spots:"])
        lines.extend(f"- {feature['id']}: {feature['next_improvement']}" for feature in report["weak"])
    else:
        lines.extend(["", "Weak spots: none"])
    return "\n".join(lines) + "\n"


def main() -> int:
    print(render_feature_quality_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
