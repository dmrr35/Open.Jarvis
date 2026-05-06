import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from open_jarvis.plugins.registry import build_plugin_registry


def _write_manifest(plugin_dir: Path, manifest: dict):
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (plugin_dir / "main.py").write_text("def on_load(context): pass\n", encoding="utf-8")


class PluginRegistryTest(TestCase):
    def test_registry_discovers_local_manifests_without_importing_code(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_manifest(
                root / "demo",
                {"id": "demo_plugin", "name": "Demo", "version": "1.0", "entrypoint": "main.py", "permissions": ["ui.notify"]},
            )

            registry = build_plugin_registry(root)

        self.assertEqual(registry["summary"]["total"], 1)
        self.assertEqual(registry["plugins"][0]["status"], "available")

    def test_duplicate_plugin_ids_are_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {"id": "same_plugin", "name": "Same", "version": "1.0", "entrypoint": "main.py", "permissions": []}
            _write_manifest(root / "one", manifest)
            _write_manifest(root / "two", {**manifest, "name": "Same Two"})

            registry = build_plugin_registry(root)

        self.assertEqual(registry["summary"]["blocked"], 2)
        self.assertTrue(all(any("duplicate plugin id" in issue for issue in plugin["issues"]) for plugin in registry["plugins"]))

    def test_malformed_manifest_is_blocked_not_fatal(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken = root / "broken"
            broken.mkdir()
            (broken / "plugin.json").write_text("{not-json", encoding="utf-8")

            registry = build_plugin_registry(root)

        self.assertEqual(registry["summary"]["blocked"], 1)
        self.assertTrue(registry["plugins"][0]["issues"])

    def test_stale_state_is_reported_missing(self):
        with TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            state_file.write_text('{"plugins":{"gone_plugin":{"enabled":true,"path":"missing"}},"audit":[]}', encoding="utf-8")

            registry = build_plugin_registry(Path(tmp) / "plugins", state_file=state_file)

        self.assertEqual(registry["summary"]["missing"], 1)
        self.assertEqual(registry["plugins"][0]["status"], "missing")
