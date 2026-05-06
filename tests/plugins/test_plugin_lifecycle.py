import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from open_jarvis.plugins.loader import dispatch_plugin_command, load_enabled_plugins, shutdown_plugins
from open_jarvis.plugins.registry import build_plugin_registry


class PluginLifecycleTest(TestCase):
    def test_command_and_shutdown_hooks_are_best_effort(self):
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
                "def on_load(context): pass\n"
                "def on_enable(context): pass\n"
                "def on_command(command, context): context.notify(command)\n"
                "def on_shutdown(context): context.emit_event('shutdown', 'bye')\n",
                encoding="utf-8",
            )
            state.write_text('{"plugins":{"demo_plugin":{"enabled":true}},"audit":[]}', encoding="utf-8")
            loaded = load_enabled_plugins(build_plugin_registry(root, state_file=state))["plugins"]

            command_results = dispatch_plugin_command(loaded, "hello")
            shutdown_results = shutdown_plugins(loaded)

        self.assertEqual(command_results[0]["status"], "ok")
        self.assertEqual(shutdown_results[0]["status"], "ok")
        self.assertEqual(loaded[0]["context"].notifications[0]["message"], "hello")

    def test_hook_failure_marks_result_without_stopping_dispatch(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            plugin = root / "broken"
            plugin.mkdir()
            (plugin / "plugin.json").write_text(
                json.dumps({"id": "broken_plugin", "name": "Broken", "version": "1.0", "entrypoint": "main.py", "permissions": []}),
                encoding="utf-8",
            )
            (plugin / "main.py").write_text("def on_command(command, context):\n    raise RuntimeError('nope')\n", encoding="utf-8")
            state.write_text('{"plugins":{"broken_plugin":{"enabled":true}},"audit":[]}', encoding="utf-8")
            loaded = load_enabled_plugins(build_plugin_registry(root, state_file=state))["plugins"]

            command_results = dispatch_plugin_command(loaded, "hello")

        self.assertEqual(command_results[0]["status"], "failed")
        self.assertIn("RuntimeError", command_results[0]["error"])
