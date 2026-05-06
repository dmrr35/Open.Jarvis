from pathlib import Path
from unittest import TestCase

from open_jarvis.plugins.context import build_plugin_context
from open_jarvis.plugins.errors import PluginPermissionError


class PluginContextTest(TestCase):
    def test_notify_requires_permission_and_masks_secrets(self):
        context = build_plugin_context("demo", Path("."), ["ui.notify"])

        notification = context.notify("GROQ_API_KEY=abc123", level="warning")

        self.assertEqual(notification["message"], "GROQ_API_KEY=***")
        self.assertEqual(context.notifications[0]["level"], "warning")

    def test_notify_denies_missing_permission(self):
        context = build_plugin_context("demo", Path("."), [])

        with self.assertRaises(PluginPermissionError):
            context.notify("hello")

    def test_register_command_requires_permission(self):
        context = build_plugin_context("demo", Path("."), ["commands.register"])

        result = context.register_command("demo command", {"token": "secret"})

        self.assertEqual(result["name"], "demo command")
        self.assertEqual(result["metadata"]["token"], "***")

    def test_privileged_facades_deny_without_permissions(self):
        context = build_plugin_context("demo", Path("."), [])

        with self.assertRaises(PluginPermissionError):
            context.request_filesystem_read("notes.txt")

    def test_privileged_facades_are_safe_stubs_when_permitted(self):
        context = build_plugin_context("demo", Path("."), ["memory.read", "groq.request"])

        memory = context.request_memory_read("notes")
        provider = context.request_provider("groq", {"api_key": "secret"})

        self.assertEqual(memory["status"], "unavailable")
        self.assertEqual(provider["payload"]["api_key"], "***")
