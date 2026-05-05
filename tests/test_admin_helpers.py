import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from jarvis_admin import (
    build_health_checks,
    build_known_limitations,
    build_onboarding_steps,
    build_settings_guide,
    format_actionable_message,
    read_env_settings,
    write_env_settings,
)


class AdminHelpersTest(unittest.TestCase):
    def test_format_actionable_message_uses_why_and_fix_sections(self):
        message = format_actionable_message(
            "Groq API key is missing",
            "The assistant cannot route AI commands.",
            "Add GROQ_API_KEY to your .env file.",
        )

        self.assertIn("Reason:", message)
        self.assertIn("Next step:", message)
        self.assertIn("Groq API key is missing", message)

    def test_build_health_checks_marks_missing_groq_as_warning(self):
        checks = build_health_checks(env={})
        groq = next(item for item in checks if item["id"] == "groq_api")

        self.assertEqual(groq["severity"], "warning")
        self.assertIn("local rule commands still work", groq["detail"])
        self.assertIn("GROQ_API_KEY", groq["fix"])

    def test_build_health_checks_marks_spotify_as_warning_when_missing(self):
        checks = build_health_checks(env={})
        spotify = next(item for item in checks if item["id"] == "spotify")

        self.assertEqual(spotify["severity"], "warning")
        self.assertIn("SPOTIFY_CLIENT_ID", spotify["fix"])

    def test_build_settings_guide_exposes_safe_defaults(self):
        guide = build_settings_guide()
        wake_word = next(item for item in guide if item["key"] == "JARVIS_WAKE_WORD")

        self.assertEqual(wake_word["safe_default"], "jarvis")
        self.assertIn("Safe default", wake_word["description"])

    def test_build_onboarding_steps_reports_ready_connections(self):
        env = {
            "GROQ_API_KEY": "sk-test-1234567890",
            "SPOTIFY_CLIENT_ID": "client",
            "SPOTIFY_CLIENT_SECRET": "secret",
        }
        steps = build_onboarding_steps(env=env)

        groq = next(item for item in steps if item["id"] == "groq")
        spotify = next(item for item in steps if item["id"] == "spotify")

        self.assertEqual(groq["status"], "ready")
        self.assertEqual(spotify["status"], "ready")

    def test_build_known_limitations_mentions_planned_solution(self):
        limitations = build_known_limitations()

        self.assertTrue(any(item["planned_solution"] for item in limitations))
        self.assertTrue(all(item.get("difficulty") for item in limitations))
        self.assertTrue(all(item.get("owner") for item in limitations))
        self.assertTrue(all(item.get("target") for item in limitations))

    def test_read_and_write_env_settings_round_trip(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            write_env_settings(
                {
                    "JARVIS_WAKE_WORD": "jarvis",
                    "GROQ_API_KEY": "abc123",
                    "SPOTIFY_CLIENT_ID": "client",
                },
                path=path,
            )
            settings = read_env_settings(path=path)

            self.assertEqual(settings["JARVIS_WAKE_WORD"], "jarvis")
            self.assertEqual(settings["GROQ_API_KEY"], "abc123")
            self.assertEqual(settings["SPOTIFY_CLIENT_ID"], "client")


if __name__ == "__main__":
    unittest.main()
