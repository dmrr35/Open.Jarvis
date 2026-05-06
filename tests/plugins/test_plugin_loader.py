import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from open_jarvis.plugins.loader import load_enabled_plugins
from open_jarvis.plugins.registry import build_plugin_registry


class PluginLoaderTest(TestCase):
    def test_loader_skips_disabled_plugins(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "demo"
            plugin.mkdir()
            (plugin / "plugin.json").write_text(
                json.dumps({"id": "demo_plugin", "name": "Demo", "version": "1.0", "entrypoint": "main.py", "permissions": []}),
                encoding="utf-8",
            )
            (plugin / "main.py").write_text("raise RuntimeError('should not import')\n", encoding="utf-8")
            registry = build_plugin_registry(root)

            loaded = load_enabled_plugins(registry)

        self.assertEqual(loaded["summary"]["disabled"], 1)
        self.assertEqual(loaded["summary"]["failed"], 0)

    def test_loader_imports_enabled_plugin_and_calls_lifecycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            plugin = root / "demo"
            plugin.mkdir()
            (plugin / "plugin.json").write_text(
                json.dumps({"id": "demo_plugin", "name": "Demo", "version": "1.0", "entrypoint": "main.py", "permissions": ["ui.notify"]}),
                encoding="utf-8",
            )
            (plugin / "main.py").write_text(
                "def on_load(context):\n    context.emit_event('load', 'loaded')\n\ndef on_enable(context):\n    context.notify('enabled')\n",
                encoding="utf-8",
            )
            state.write_text('{"plugins":{"demo_plugin":{"enabled":true}},"audit":[]}', encoding="utf-8")
            registry = build_plugin_registry(root, state_file=state)

            loaded = load_enabled_plugins(registry)

        self.assertEqual(loaded["summary"]["loaded"], 1)
        self.assertEqual(loaded["plugins"][0]["hook_results"][0]["status"], "ok")
        self.assertEqual(loaded["plugins"][0]["context"].notifications[0]["message"], "enabled")

    def test_loader_isolates_import_failures(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            plugin = root / "broken"
            plugin.mkdir()
            (plugin / "plugin.json").write_text(
                json.dumps({"id": "broken_plugin", "name": "Broken", "version": "1.0", "entrypoint": "main.py", "permissions": []}),
                encoding="utf-8",
            )
            (plugin / "main.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")
            state.write_text('{"plugins":{"broken_plugin":{"enabled":true}},"audit":[]}', encoding="utf-8")
            registry = build_plugin_registry(root, state_file=state)

            loaded = load_enabled_plugins(registry)

        self.assertEqual(loaded["summary"]["failed"], 1)
        self.assertEqual(loaded["plugins"][0]["status"], "failed")
