"""LLM provider selection with local fallback support."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

VALID_AI_MODES = {"auto", "free_cloud", "offline", "rules"}


def _clean_mode(value: str | None) -> str:
    mode = str(value or "auto").strip().lower()
    return mode if mode in VALID_AI_MODES else "auto"


def select_llm_provider(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Choose the best available routing provider without making network calls."""

    env = env or {}
    if str(env.get("GROQ_API_KEY", "")).strip():
        return {"provider": "groq", "mode": "free_cloud", "reason": "GROQ_API_KEY is configured"}
    if str(env.get("JARVIS_LOCAL_LLM_URL", "")).strip():
        return {"provider": "local", "mode": "offline", "reason": "Local LLM endpoint is configured"}
    return {"provider": "rules", "mode": "rules", "reason": "No LLM credentials or local endpoint configured"}


def resolve_ai_mode(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Resolve the requested AI mode into the provider currently allowed to run."""

    env = env or {}
    requested = _clean_mode(env.get("JARVIS_AI_MODE"))
    if requested == "rules":
        return {"provider": "rules", "mode": "rules", "reason": "JARVIS_AI_MODE forces local rules"}
    if requested == "offline":
        if str(env.get("JARVIS_LOCAL_LLM_URL", "")).strip():
            return {"provider": "local", "mode": "offline", "reason": "JARVIS_AI_MODE forces local LLM"}
        return {"provider": "rules", "mode": "rules", "reason": "Offline mode requested without a local LLM endpoint"}
    if requested == "free_cloud":
        if str(env.get("GROQ_API_KEY", "")).strip():
            return {"provider": "groq", "mode": "free_cloud", "reason": "JARVIS_AI_MODE forces Groq free cloud"}
        return {"provider": "rules", "mode": "rules", "reason": "Free cloud mode requested without GROQ_API_KEY"}
    selected = select_llm_provider(env)
    return {**selected, "reason": f"auto: {selected['reason']}"}


def build_provider_result(
    *,
    ok: bool,
    provider: str,
    mode: str,
    action: dict[str, Any] | None = None,
    error: str | None = None,
    latency_ms: float | None = None,
) -> dict[str, Any]:
    """Return a stable provider result envelope for future router implementations."""

    return {
        "ok": ok,
        "provider": provider,
        "mode": mode,
        "action": action,
        "error": error,
        "latency_ms": latency_ms,
    }


def describe_ai_status(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return compact labels that can be shown in the UI."""

    resolved = resolve_ai_mode(env)
    return {
        "provider": resolved["provider"].upper(),
        "mode": resolved["mode"].upper().replace("_", " "),
        "reason": resolved["reason"],
    }
