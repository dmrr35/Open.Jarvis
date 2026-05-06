import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from open_jarvis.plugins.loader import load_enabled_plugins
from open_jarvis.plugins.registry import build_plugin_registry


class PluginFailureIsolationTest(TestCase):
    def test_one_failed_plugin_does_not_block_another_plugin(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state.json"
            good = root / "good"
            bad = root / "bad"
            good.mkdir()
            bad.mkdir()
            (good / "plugin.json").write_text(
                json.dumps({"id": "good_plugin", "name": "Good", "version": "1.0", "entrypoint": "main.py", "permissions": []}),
                encoding="utf-8",
            )
            (good / "main.py").write_text("def on_load(context): pass\ndef on_enable(context): pass\n", encoding="utf-8")
            (bad / "plugin.json").write_text(
                json.dumps({"id": "bad_plugin", "name": "Bad", "version": "1.0", "entrypoint": "main.py", "permissions": []}),
                encoding="utf-8",
            )
            (bad / "main.py").write_text("raise RuntimeError('bad plugin')\n", encoding="utf-8")
            state.write_text('{"plugins":{"good_plugin":{"enabled":true},"bad_plugin":{"enabled":true}},"audit":[]}', encoding="utf-8")

            loaded = load_enabled_plugins(build_plugin_registry(root, state_file=state))

        self.assertEqual(loaded["summary"]["loaded"], 1)
        self.assertEqual(loaded["summary"]["failed"], 1)
