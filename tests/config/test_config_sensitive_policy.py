import unittest

from open_jarvis.config.sensitive import build_sensitive_status, is_sensitive_key, mask_sensitive_setting, reject_sensitive_payload


class SensitivePolicyTests(unittest.TestCase):
    def test_sensitive_detection_covers_known_and_pattern_keys(self):
        self.assertTrue(is_sensitive_key("GROQ_API_KEY"))
        self.assertTrue(is_sensitive_key("SPOTIFY_REFRESH_TOKEN"))
        self.assertTrue(is_sensitive_key("custom_password"))
        self.assertFalse(is_sensitive_key("voice.wake_word"))

    def test_sensitive_status_exposes_presence_without_raw_values(self):
        status = build_sensitive_status({"GROQ_API_KEY": "value", "SPOTIFY_CLIENT_SECRET": ""})

        self.assertEqual(status["GROQ_API_KEY"], "configured")
        self.assertEqual(status["SPOTIFY_CLIENT_SECRET"], "missing")
        self.assertNotIn("value", str(status))

    def test_reject_sensitive_payload_blocks_nested_keys(self):
        errors = reject_sensitive_payload({"ai": {"GROQ_API_KEY": "value"}, "voice": {"wake_word": "friday"}})

        self.assertTrue(errors)
        self.assertIn("GROQ_API_KEY", errors[0])

    def test_mask_sensitive_setting_never_returns_raw_value(self):
        self.assertEqual(mask_sensitive_setting("value"), "configured")
        self.assertEqual(mask_sensitive_setting(""), "missing")


if __name__ == "__main__":
    unittest.main()
