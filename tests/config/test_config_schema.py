import unittest

from open_jarvis.config.defaults import build_default_config
from open_jarvis.config.schema import FIELD_DEFINITIONS, get_field


class ConfigSchemaTests(unittest.TestCase):
    def test_defaults_are_category_based_and_backward_compatible(self):
        config = build_default_config()

        self.assertEqual(config["general"]["theme"], "system")
        self.assertEqual(config["ai"]["mode"], "auto")
        self.assertFalse(config["ai"]["groq_enabled"])
        self.assertEqual(config["voice"]["wake_word"], "jarvis")
        self.assertTrue(config["voice"]["voice_enabled"])
        self.assertTrue(config["voice"]["offline_stt_enabled"])
        self.assertFalse(config["spotify"]["enabled"])
        self.assertFalse(config["privacy"]["privacy_mode"])

    def test_schema_exposes_types_allowed_values_and_env_mapping(self):
        ai_mode = get_field("ai.mode")
        permission = get_field("plugins.permission_profile")

        self.assertEqual(ai_mode.value_type, "string")
        self.assertEqual(ai_mode.env_var, "JARVIS_AI_MODE")
        self.assertEqual(ai_mode.allowed_values, ("auto", "free_cloud", "offline", "rules", "local", "cloud"))
        self.assertEqual(permission.allowed_values, ("safe", "normal", "admin"))

    def test_secret_fields_are_not_configurable_settings(self):
        env_names = {field.env_var for field in FIELD_DEFINITIONS.values() if field.env_var}

        self.assertNotIn("GROQ_API_KEY", env_names)
        self.assertNotIn("SPOTIFY_CLIENT_SECRET", env_names)
        self.assertNotIn("JARVIS_RELEASE_SIGNING_KEY", env_names)


if __name__ == "__main__":
    unittest.main()
