import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from open_jarvis.config.paths import ConfigPaths, resolve_config_paths


class ConfigPathTests(unittest.TestCase):
    def test_explicit_path_is_used_for_tests_without_creating_file(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            paths = resolve_config_paths(config_path=path)

            self.assertEqual(paths.settings_file, path)
            self.assertFalse(path.exists())
            self.assertFalse(paths.portable)

    def test_env_override_path_is_supported(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "custom.json"
            paths = resolve_config_paths(env={"JARVIS_CONFIG_PATH": str(path)})

            self.assertEqual(paths.settings_file, path)

    def test_portable_marker_uses_local_config_folder(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Open.Jarvis.exe").write_text("", encoding="utf-8")
            paths = ConfigPaths.for_portable_root(root)

            self.assertTrue(paths.portable)
            self.assertEqual(paths.settings_file, root / "config" / "settings.json")

    def test_source_path_uses_user_local_directory(self):
        with TemporaryDirectory() as tmp:
            paths = resolve_config_paths(env={"LOCALAPPDATA": tmp, "APPDATA": os.path.join(tmp, "Roaming")})

            self.assertIn("Open.Jarvis", str(paths.settings_file))
            self.assertTrue(str(paths.settings_file).endswith("settings.json"))


if __name__ == "__main__":
    unittest.main()
