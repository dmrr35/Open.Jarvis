"""Domain-focused product tests split from the former monolithic product feature suite."""

from unittest import TestCase

from open_jarvis.memory.privacy_mode import build_privacy_session, mask_sensitive_text, mask_sensitive_value
from open_jarvis.memory.user_profiles import build_user_profile, merge_user_profile
from open_jarvis.plugins.permission_profiles import action_allowed, build_permission_matrix, get_active_permission_profile
from open_jarvis.ui.memory_panel import build_memory_panel, delete_note, update_preference
from open_jarvis.ui.security_center import build_security_overview


class ProductSecurityMemoryTest(TestCase):
    def test_permission_profiles_block_or_allow_risky_actions(self):
        self.assertFalse(action_allowed("shutdown", "safe"))
        self.assertTrue(action_allowed("open_web", "safe"))
        self.assertTrue(action_allowed("shutdown", "admin"))
        self.assertEqual(get_active_permission_profile({"JARVIS_PERMISSION_PROFILE": "admin"})["id"], "admin")
        self.assertEqual(get_active_permission_profile({"JARVIS_PERMISSION_PROFILE": "unknown"})["id"], "normal")

        matrix = build_permission_matrix(["open_web", "shutdown"])
        self.assertEqual(matrix["shutdown"]["safe"], "blocked")
        self.assertEqual(matrix["shutdown"]["admin"], "allowed")

    def test_security_overview_summarizes_permission_privacy_and_secret_status(self):
        overview = build_security_overview(
            {
                "JARVIS_PERMISSION_PROFILE": "safe",
                "JARVIS_PRIVACY_MODE": "true",
                "GROQ_API_KEY": "secret",
                "SPOTIFY_CLIENT_SECRET": "",
            },
            actions=["open_web", "shutdown"],
        )

        self.assertEqual(overview["profile"]["id"], "safe")
        self.assertTrue(overview["privacy"]["enabled"])
        self.assertEqual(overview["secrets"]["GROQ_API_KEY"], "CONFIGURED")
        self.assertEqual(overview["secrets"]["SPOTIFY_CLIENT_SECRET"], "MISSING")
        self.assertEqual(overview["permission_matrix"]["shutdown"]["safe"], "blocked")
        self.assertIn("shutdown", overview["confirmation_required"])

    def test_memory_panel_can_update_and_delete_user_visible_memory(self):
        memory = {"preferences": {"wake_word": "jarvis"}, "notes": ["a", "b"], "habits": {"music": 3}}

        updated = update_preference(memory, "favorite_app", "Chrome")
        trimmed = delete_note(updated, 0)
        panel = build_memory_panel(trimmed)

        self.assertEqual(panel["preferences"]["favorite_app"], "Chrome")
        self.assertEqual(panel["notes"], ["b"])
        self.assertEqual(panel["counts"]["habits"], 1)

    def test_memory_panel_exposes_privacy_controls_without_leaking_raw_secrets(self):
        memory = {
            "preferences": {"GROQ_API_KEY": "secret", "favorite_app": "Chrome"},
            "notes": [{"text": "first"}, {"text": "second"}],
            "habits": {"music": 3},
        }

        panel = build_memory_panel(memory, privacy_enabled=True)

        self.assertEqual(panel["privacy"]["memory_writes"], "disabled")
        self.assertEqual(panel["preferences"]["GROQ_API_KEY"], "***")
        self.assertEqual(panel["recent_notes"], [{"text": "first"}, {"text": "second"}])

    def test_privacy_mode_masks_sensitive_values_and_marks_ephemeral(self):
        self.assertEqual(mask_sensitive_text("GROQ_API_KEY=abc123 and token=secret"), "GROQ_API_KEY=*** and token=***")
        self.assertEqual(mask_sensitive_value({"token": "secret", "note": "PASSWORD=abc"}), {"token": "***", "note": "PASSWORD=***"})

        session = build_privacy_session(enabled=True)
        self.assertEqual(session["memory_writes"], "disabled")
        self.assertEqual(session["retention"], "ephemeral")

    def test_privacy_mode_off_keeps_normal_retention(self):
        session = build_privacy_session(enabled=False)

        self.assertEqual(session["memory_writes"], "enabled")
        self.assertEqual(session["retention"], "normal")

    def test_user_profile_merge_keeps_isolated_preferences(self):
        base = build_user_profile("ali")
        merged = merge_user_profile(base, {"wake_word": "friday", "permission_profile": "safe"})

        self.assertEqual(merged["id"], "ali")
        self.assertEqual(merged["settings"]["wake_word"], "friday")
        self.assertEqual(merged["settings"]["permission_profile"], "safe")
