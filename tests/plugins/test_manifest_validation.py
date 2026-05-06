from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from open_jarvis.plugins.manifest import derive_plugin_id, validate_plugin_manifest_schema


class PluginManifestValidationTest(TestCase):
    def test_valid_v030_manifest_passes(self):
        manifest = {
            "id": "example_plugin",
            "name": "Example Plugin",
            "version": "0.1.0",
            "entrypoint": "main.py",
            "permissions": ["commands.register", "ui.notify"],
            "enabled_by_default": False,
        }

        result = validate_plugin_manifest_schema(manifest)

        self.assertTrue(result["valid"])
        self.assertEqual(result["id"], "example_plugin")
        self.assertEqual(result["risk"], "low")

    def test_legacy_manifest_derives_id_and_permissions_with_warnings(self):
        manifest = {"name": "Legacy Plugin", "version": "1.0", "entrypoint": "main.py", "signer": "ci"}

        result = validate_plugin_manifest_schema(manifest)

        self.assertTrue(result["valid"])
        self.assertTrue(result["legacy"])
        self.assertEqual(result["id"], "legacy_plugin")
        self.assertIn("manifest id is missing; derived from name", result["warnings"])

    def test_invalid_id_is_blocked(self):
        result = validate_plugin_manifest_schema(
            {"id": "Bad Plugin", "name": "Bad", "version": "1.0", "entrypoint": "main.py", "permissions": []}
        )

        self.assertFalse(result["valid"])
        self.assertTrue(any("plugin id" in issue for issue in result["issues"]))

    def test_entrypoint_must_stay_inside_plugin_directory(self):
        with TemporaryDirectory() as tmp:
            result = validate_plugin_manifest_schema(
                {"id": "escape_plugin", "name": "Escape", "version": "1.0", "entrypoint": "../evil.py", "permissions": []},
                plugin_dir=Path(tmp),
            )

        self.assertFalse(result["valid"])
        self.assertTrue(any("entrypoint" in issue for issue in result["issues"]))

    def test_permissions_must_be_known_and_unique(self):
        result = validate_plugin_manifest_schema(
            {
                "id": "bad_permissions",
                "name": "Bad Permissions",
                "version": "1.0",
                "entrypoint": "main.py",
                "permissions": ["ui.notify", "ui.notify", "unknown.permission"],
            }
        )

        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate permission" in issue for issue in result["issues"]))
        self.assertTrue(any("unknown permission" in issue for issue in result["issues"]))

    def test_derive_plugin_id_normalizes_display_names(self):
        self.assertEqual(derive_plugin_id("Example Plugin!"), "example_plugin")
