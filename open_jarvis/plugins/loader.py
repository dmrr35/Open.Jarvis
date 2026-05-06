"""Optional plugin loader with lifecycle failure isolation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

from open_jarvis.plugins.context import PluginContext, build_plugin_context
from open_jarvis.plugins.errors import PluginLoadError, PluginRuntimeError
from open_jarvis.plugins.lifecycle import available_hooks, build_hook_result

PLUGIN_FAILURE_EXCEPTIONS = (Exception,)


def _import_plugin_module(plugin_id: str, entrypoint: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"open_jarvis_local_plugin_{plugin_id}", entrypoint)
    if spec is None or spec.loader is None:
        raise PluginLoadError("Plugin module spec could not be created.", plugin_id=plugin_id)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except PLUGIN_FAILURE_EXCEPTIONS as exc:
        raise PluginLoadError("Plugin import failed.", plugin_id=plugin_id, issues=[exc.__class__.__name__]) from exc
    return module


def call_plugin_hook(module: ModuleType, plugin_id: str, hook: str, *args: Any) -> dict[str, str]:
    """Call a hook and convert failures into structured results."""

    callback = getattr(module, hook, None)
    if not callable(callback):
        return build_hook_result(plugin_id, hook, "missing")
    try:
        callback(*args)
    except PLUGIN_FAILURE_EXCEPTIONS as exc:
        raise PluginRuntimeError(f"Plugin hook failed: {hook}", plugin_id=plugin_id, issues=[exc.__class__.__name__]) from exc
    return build_hook_result(plugin_id, hook, "ok")


def load_plugin(entry: dict[str, Any], *, logger: Any = None) -> dict[str, Any]:
    """Load one enabled plugin entry while isolating import and hook failures."""

    plugin_id = str(entry.get("id", ""))
    if entry.get("status") == "blocked" or entry.get("issues"):
        return {"id": plugin_id, "status": "blocked", "issues": list(entry.get("issues", [])), "hooks": []}
    if not entry.get("enabled"):
        return {"id": plugin_id, "status": "disabled", "issues": [], "hooks": []}

    manifest = entry.get("manifest", {})
    plugin_dir = Path(str(entry.get("path", "")))
    entrypoint = (plugin_dir / str(manifest.get("entrypoint", ""))).resolve()
    context = build_plugin_context(plugin_id, plugin_dir, list(entry.get("permissions", [])), logger=logger)
    try:
        module = _import_plugin_module(plugin_id, entrypoint)
        hooks = available_hooks(module)
        results = [
            call_plugin_hook(module, plugin_id, "on_load", context),
            call_plugin_hook(module, plugin_id, "on_enable", context),
        ]
    except (PluginLoadError, PluginRuntimeError) as exc:
        return {"id": plugin_id, "status": "failed", "issues": exc.issues or [str(exc)], "hooks": [], "diagnostic": exc.as_diagnostic()}

    return {"id": plugin_id, "status": "loaded", "issues": [], "hooks": hooks, "hook_results": results, "context": context, "module": module}


def load_enabled_plugins(registry: dict[str, Any], *, logger: Any = None) -> dict[str, Any]:
    """Load enabled plugins from a registry without letting one failure stop others."""

    loaded = [load_plugin(entry, logger=logger) for entry in registry.get("plugins", [])]
    return {
        "plugins": loaded,
        "summary": {
            "loaded": sum(1 for item in loaded if item["status"] == "loaded"),
            "failed": sum(1 for item in loaded if item["status"] == "failed"),
            "blocked": sum(1 for item in loaded if item["status"] == "blocked"),
            "disabled": sum(1 for item in loaded if item["status"] == "disabled"),
        },
    }


def dispatch_plugin_command(loaded_plugins: list[dict[str, Any]], command: str) -> list[dict[str, str]]:
    """Dispatch a command to loaded plugin on_command hooks."""

    results: list[dict[str, str]] = []
    for plugin in loaded_plugins:
        if plugin.get("status") != "loaded":
            continue
        module = plugin["module"]
        context: PluginContext = plugin["context"]
        plugin_id = str(plugin["id"])
        try:
            results.append(call_plugin_hook(module, plugin_id, "on_command", command, context))
        except PluginRuntimeError as exc:
            results.append(build_hook_result(plugin_id, "on_command", "failed", ",".join(exc.issues) or str(exc)))
    return results


def shutdown_plugins(loaded_plugins: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Best-effort shutdown for loaded plugins."""

    results: list[dict[str, str]] = []
    for plugin in loaded_plugins:
        if plugin.get("status") != "loaded":
            continue
        module = plugin["module"]
        context: PluginContext = plugin["context"]
        plugin_id = str(plugin["id"])
        try:
            results.append(call_plugin_hook(module, plugin_id, "on_shutdown", context))
        except PluginRuntimeError as exc:
            results.append(build_hook_result(plugin_id, "on_shutdown", "failed", ",".join(exc.issues) or str(exc)))
    return results
