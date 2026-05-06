from pathlib import Path
from unittest import TestCase

from open_jarvis.plugins.context import build_plugin_context
from open_jarvis.plugins.errors import PluginPermissionError
from open_jarvis.plugins.manifest import validate_plugin_manifest_schema


class PluginSecurityBoundariesTest(TestCase):
    def test_network_and_process_permissions_are_not_available_by_default(self):
        result = validate_plugin_manifest_schema(
            {
                "id": "risky_plugin",
                "name": "Risky",
                "version": "1.0",
                "entrypoint": "main.py",
                "permissions": ["network.request", "process.spawn"],
            }
        )

        self.assertFalse(result["valid"])
        self.assertIn("network.request", result["blocked_permissions"])
        self.assertIn("process.spawn", result["blocked_permissions"])

    def test_context_does_not_expose_raw_environment(self):
        context = build_plugin_context("demo", Path("."), [])

        self.assertFalse(hasattr(context, "environ"))
        self.assertFalse(hasattr(context, "groq_client"))
        self.assertFalse(hasattr(context, "spotify_client"))

    def test_filesystem_write_requires_critical_permission_even_as_stub(self):
        context = build_plugin_context("demo", Path("."), [])

        with self.assertRaises(PluginPermissionError):
            context.request_filesystem_write("out.txt", "hello")
