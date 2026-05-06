from unittest import TestCase

from open_jarvis.plugins.permissions import (
    highest_permission_risk,
    list_plugin_permissions,
    permission_risk,
    validate_plugin_permissions,
)


class PluginPermissionsTest(TestCase):
    def test_known_permissions_are_registered(self):
        permissions = {item["name"]: item for item in list_plugin_permissions()}

        self.assertEqual(permissions["commands.register"]["risk"], "low")
        self.assertEqual(permissions["filesystem.write"]["risk"], "critical")

    def test_unknown_permission_is_blocked(self):
        result = validate_plugin_permissions(["unknown.permission"])

        self.assertFalse(result["valid"])
        self.assertEqual(result["blocked_permissions"], ["unknown.permission"])

    def test_high_risk_permission_requires_explicit_approval(self):
        denied = validate_plugin_permissions(["network.request"])
        approved = validate_plugin_permissions(["network.request"], policy={"approved_permissions": ["network.request"]})

        self.assertFalse(denied["valid"])
        self.assertTrue(approved["valid"])
        self.assertIn("risky permission explicitly approved: network.request", approved["warnings"])

    def test_critical_permission_is_blocked_by_default(self):
        result = validate_plugin_permissions(["process.spawn"])

        self.assertFalse(result["valid"])
        self.assertTrue(any("critical permission" in issue for issue in result["issues"]))

    def test_highest_permission_risk_is_deterministic(self):
        self.assertEqual(highest_permission_risk(["ui.notify", "memory.read", "filesystem.write"]), "critical")
        self.assertEqual(permission_risk("missing.permission"), "critical")
