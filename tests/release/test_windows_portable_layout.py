from unittest import TestCase

from open_jarvis.release.portable_policy import (
    DEFAULT_APP_NAME,
    GUIDANCE_FOLDERS,
    REQUIRED_ROOT_FILES,
    build_artifact_name,
    expected_executable_path,
    is_denied_portable_path,
)


class WindowsPortableLayoutTest(TestCase):
    def test_default_artifact_name_and_executable_path_are_stable(self):
        self.assertEqual(DEFAULT_APP_NAME, "Open.Jarvis")
        self.assertEqual(build_artifact_name("v0.5.0"), "Open.Jarvis-v0.5.0-windows-portable")
        self.assertEqual(expected_executable_path(), "Open.Jarvis/Open.Jarvis.exe")

    def test_required_files_and_guidance_folders_are_declared(self):
        self.assertIn("README_FIRST.txt", REQUIRED_ROOT_FILES)
        self.assertIn("LICENSE", REQUIRED_ROOT_FILES)
        self.assertIn(".env.example", REQUIRED_ROOT_FILES)
        self.assertIn("plugins", GUIDANCE_FOLDERS)
        self.assertIn("config", GUIDANCE_FOLDERS)
        self.assertIn("optional_models", GUIDANCE_FOLDERS)

    def test_policy_denies_private_and_generated_paths(self):
        denied = [".env", "memory.json", "logs/jarvis.log", "__pycache__/x.pyc", "build/tmp.txt", "secret-token.txt"]

        for path in denied:
            with self.subTest(path=path):
                self.assertTrue(is_denied_portable_path(path)["denied"])

    def test_expected_executable_is_allowed_but_unexpected_exe_is_denied(self):
        self.assertFalse(is_denied_portable_path("Open.Jarvis/Open.Jarvis.exe")["denied"])
        self.assertTrue(is_denied_portable_path("tools/helper.exe")["denied"])
