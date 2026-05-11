import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from open_jarvis.config.manager import ConfigManager
from open_jarvis.config.paths import ConfigPaths
from open_jarvis.ui.settings_panel import SettingsPanelModel, build_settings_view_model, collect_editable_settings


class SettingsPanelViewModelTests(unittest.TestCase):
    def test_view_model_groups_editable_settings_and_secret_statuses(self):
        model = build_settings_view_model(
            config={
                "general": {"theme": "system", "language": "en", "debug_mode": False, "start_minimized": False},
                "ai": {"mode": "auto", "groq_enabled": False, "local_llm_url": "", "cloud_fallback_enabled": True},
                "voice": {"voice_enabled": True, "wake_word": "jarvis"},
                "spotify": {"enabled": False, "redirect_uri": "http://127.0.0.1:8888/callback"},
            },
            secret_status={"GROQ_API_KEY": "configured", "SPOTIFY_CLIENT_SECRET": "missing"},
        )

        self.assertIn("General", model["groups"])
        self.assertIn("AI Provider", model["groups"])
        self.assertIn("Secrets", model["groups"])
        self.assertFalse(any(row.get("editable") for row in model["groups"]["Secrets"]))
        self.assertNotIn("raw", str(model).lower())

    def test_collect_editable_settings_omits_secret_rows(self):
        updates = collect_editable_settings(
            [
                {"key": "voice.wake_word", "value": "friday", "editable": True},
                {"key": "GROQ_API_KEY", "value": "value", "editable": False},
            ]
        )

        self.assertEqual(updates, {"voice.wake_word": "friday"})
        self.assertNotIn("GROQ_API_KEY", updates)

    def test_settings_panel_model_saves_to_settings_json_not_env(self):
        with TemporaryDirectory() as tmp:
            manager = ConfigManager(paths=ConfigPaths(config_dir=Path(tmp), settings_file=Path(tmp) / "settings.json"), env={})
            model = SettingsPanelModel(manager)

            result = model.save({"voice.wake_word": "friday"})

            self.assertEqual(result["status"], "saved")
            self.assertTrue((Path(tmp) / "settings.json").exists())
            self.assertFalse((Path(tmp) / ".env").exists())

    def test_settings_dialog_no_longer_writes_env_files(self):
        content = Path("open_jarvis/ui/ui_dialogs.py").read_text(encoding="utf-8")

        self.assertNotIn("write_env_settings(settings)", content)
        self.assertIn("SettingsPanelModel", content)


if __name__ == "__main__":
    unittest.main()
