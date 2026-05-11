import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from open_jarvis.config.manager import ConfigManager
from open_jarvis.config.paths import ConfigPaths


class ConfigPrecedenceTests(unittest.TestCase):
    def test_env_overrides_defaults_and_user_config_overrides_env_for_non_secrets(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text(json.dumps({"settings": {"voice": {"wake_word": "friday"}}}), encoding="utf-8")
            manager = ConfigManager(
                paths=ConfigPaths(config_dir=Path(tmp), settings_file=path),
                env={"JARVIS_WAKE_WORD": "computer", "JARVIS_ENABLE_GROQ": "true"},
            )

            config = manager.load()

            self.assertEqual(config["voice"]["wake_word"], "friday")
            self.assertTrue(config["ai"]["groq_enabled"])
            self.assertTrue(any("JARVIS_WAKE_WORD" in item for item in manager.diagnostics()["conflicts"]))

    def test_invalid_env_value_falls_back_without_crashing(self):
        with TemporaryDirectory() as tmp:
            manager = ConfigManager(
                paths=ConfigPaths(config_dir=Path(tmp), settings_file=Path(tmp) / "settings.json"),
                env={"JARVIS_ACTIVE_TIMEOUT": "not-a-number"},
            )

            config = manager.load()

            self.assertEqual(config["voice"]["active_timeout"], 60)
            self.assertTrue(manager.diagnostics()["warnings"])

    def test_secret_from_config_file_is_rejected_but_env_secret_status_survives(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text(json.dumps({"settings": {"ai": {"GROQ_API_KEY": "file-value"}}}), encoding="utf-8")
            manager = ConfigManager(
                paths=ConfigPaths(config_dir=Path(tmp), settings_file=path),
                env={"GROQ_API_KEY": "env-value"},
            )

            config = manager.load()

            self.assertNotIn("GROQ_API_KEY", config["ai"])
            self.assertEqual(manager.get_secret_status("GROQ_API_KEY"), "configured")
            self.assertNotIn("env-value", str(manager.export_safe()))


if __name__ == "__main__":
    unittest.main()
