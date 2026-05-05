"""Provider health checks for free-first AI routing."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

Fetcher = Callable[[str, float], Any]


def _is_configured(value: str | None) -> bool:
    return bool(str(value or "").strip()) and "YOUR_" not in str(value or "")


def _base_check(provider_id: str, title: str, severity: str, detail: str, fix: str, fix_command: str = "notepad .env") -> dict[str, str]:
    return {
        "id": provider_id,
        "severity": severity,
        "title": title,
        "detail": detail,
        "fix": fix,
        "fix_command": fix_command,
    }


def _default_fetcher(url: str, timeout: float) -> Any:
    return urllib.request.urlopen(url, timeout=timeout)


def probe_local_llm(
    base_url: str,
    *,
    timeout: float = 1.5,
    fetcher: Fetcher = _default_fetcher,
) -> dict[str, str]:
    """Probe a local LLM endpoint with a short timeout."""

    cleaned_url = str(base_url or "").strip().rstrip("/")
    if not cleaned_url:
        return _base_check(
            "provider_local_llm",
            "Local LLM provider",
            "info",
            "No local LLM endpoint is configured.",
            "Set JARVIS_LOCAL_LLM_URL only if you use Ollama, LM Studio, or another local endpoint.",
        )

    started = time.perf_counter()
    try:
        fetcher(cleaned_url, timeout)
    except (OSError, urllib.error.URLError, ValueError) as exc:
        return _base_check(
            "provider_local_llm",
            "Local LLM provider",
            "warning",
            f"Local LLM endpoint is configured but not reachable: {exc}.",
            "Start your local LLM server or clear JARVIS_LOCAL_LLM_URL.",
        )

    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    return _base_check(
        "provider_local_llm",
        "Local LLM provider",
        "ok",
        f"Local LLM endpoint is reachable in {latency_ms} ms.",
        "No action needed.",
    )


def build_provider_health_checks(
    env: Mapping[str, str] | None = None,
    *,
    probe_local: bool = False,
    fetcher: Fetcher = _default_fetcher,
) -> list[dict[str, str]]:
    """Build non-invasive provider checks for health reports and UI panels."""

    env = env or {}
    checks = []

    if _is_configured(env.get("GROQ_API_KEY")):
        checks.append(
            _base_check(
                "provider_groq",
                "Groq provider",
                "ok",
                "Groq API key is configured. Connectivity is checked when an AI command runs.",
                "No action needed.",
            )
        )
    else:
        checks.append(
            _base_check(
                "provider_groq",
                "Groq provider",
                "info",
                "Groq API key is not configured; local rule commands still work.",
                "Add GROQ_API_KEY only if you want free-cloud AI routing.",
            )
        )

    if _is_configured(env.get("GEMINI_API_KEY")):
        checks.append(
            _base_check(
                "provider_gemini",
                "Gemini provider",
                "ok",
                "Gemini API key is configured for optional future vision flows.",
                "No action needed.",
            )
        )
    else:
        checks.append(
            _base_check(
                "provider_gemini",
                "Gemini provider",
                "info",
                "Gemini API key is not configured; this is fine unless you enable Gemini-backed vision.",
                "Add GEMINI_API_KEY only if you need Gemini-backed flows.",
            )
        )

    local_url = str(env.get("JARVIS_LOCAL_LLM_URL", "")).strip()
    if probe_local:
        checks.append(probe_local_llm(local_url, fetcher=fetcher))
    elif local_url:
        checks.append(
            _base_check(
                "provider_local_llm",
                "Local LLM provider",
                "ok",
                "Local LLM endpoint is configured. Use explicit probing before relying on it.",
                "Run python kontrol.py --probe-providers to test local connectivity.",
                "python kontrol.py --probe-providers --no-pause",
            )
        )
    else:
        checks.append(
            _base_check(
                "provider_local_llm",
                "Local LLM provider",
                "info",
                "No local LLM endpoint is configured.",
                "Set JARVIS_LOCAL_LLM_URL only if you use a local provider.",
            )
        )

    return checks
