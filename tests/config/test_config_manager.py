import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from open_jarvis.config.manager import ConfigManager
from open_jarvis.config.paths import ConfigPaths


class ConfigManagerTests(unittest.TestCase):
    def _manager(self, tmp: str, env: dict[str, str] | None = None) -> ConfigManager:
        return ConfigManager(paths=ConfigPaths(config_dir=Path(tmp), settings_file=Path(tmp) / "settings.json"), env=env or {})

    def test_missing_config_loads_defaults_without_writing_file(self):
        with TemporaryDirectory() as tmp:
            manager = self._manager(tmp)
            config = manager.load()

            self.assertEqual(config["voice"]["wake_word"], "jarvis")
            self.assertFalse((Path(tmp) / "settings.json").exists())
            self.assertFalse(manager.diagnostics()["config_exists"])

    def test_save_and_reset_round_trip_non_secret_settings(self):
        with TemporaryDirectory() as tmp:
            manager = self._manager(tmp)
            manager.load()
            manager.set("voice.wake_word", "friday")
            manager.set("privacy.privacy_mode", True)
            manager.save()

            reloaded = self._manager(tmp).load()
            self.assertEqual(reloaded["voice"]["wake_word"], "friday")
            self.assertTrue(reloaded["privacy"]["privacy_mode"])

            manager.reset()
            self.assertEqual(manager.get("voice.wake_word"), "jarvis")

    def test_corrupted_config_falls_back_and_reports_diagnostic(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text("{not-json", encoding="utf-8")
            manager = self._manager(tmp)

            config = manager.load()

            self.assertEqual(config["voice"]["wake_word"], "jarvis")
            self.assertIn("load_error", manager.diagnostics())

    def test_save_rejects_secret_keys(self):
        with TemporaryDirectory() as tmp:
            manager = self._manager(tmp)
            manager.load()
            manager._config["ai"]["GROQ_API_KEY"] = "value"

            with self.assertRaises(ValueError):
                manager.save()

            self.assertFalse((Path(tmp) / "settings.json").exists())

    def test_export_safe_omits_raw_secret_values(self):
        with TemporaryDirectory() as tmp:
            manager = self._manager(tmp, env={"GROQ_API_KEY": "value", "SPOTIFY_CLIENT_SECRET": "value"})
            manager.load()
            export = manager.export_safe()

            text = json.dumps(export)
            self.assertIn('"configured"', text)
            self.assertNotIn("value", text)


if __name__ == "__main__":
    unittest.main()
