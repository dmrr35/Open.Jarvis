import unittest

from open_jarvis.config.defaults import build_default_config
from open_jarvis.config.validation import parse_bool, validate_config


class ConfigValidationTests(unittest.TestCase):
    def test_parse_bool_accepts_safe_env_forms(self):
        self.assertTrue(parse_bool("1", default=False))
        self.assertTrue(parse_bool("yes", default=False))
        self.assertFalse(parse_bool("off", default=True))
        self.assertTrue(parse_bool("not-a-bool", default=True))

    def test_invalid_values_fall_back_with_warnings(self):
        result = validate_config(
            {
                "general": {"theme": "neon"},
                "voice": {"wake_word": "", "active_timeout": "-1"},
                "plugins": {"permission_profile": "root"},
            }
        )

        self.assertTrue(result.valid)
        self.assertGreaterEqual(len(result.warnings), 4)
        self.assertEqual(result.normalized["general"]["theme"], build_default_config()["general"]["theme"])
        self.assertEqual(result.normalized["voice"]["wake_word"], "jarvis")
        self.assertEqual(result.normalized["voice"]["active_timeout"], 60)
        self.assertEqual(result.normalized["plugins"]["permission_profile"], "normal")

    def test_sensitive_fields_are_rejected(self):
        result = validate_config({"ai": {"GROQ_API_KEY": "not-for-files"}})

        self.assertFalse(result.valid)
        self.assertTrue(any("sensitive" in error.lower() for error in result.errors))


if __name__ == "__main__":
    unittest.main()
