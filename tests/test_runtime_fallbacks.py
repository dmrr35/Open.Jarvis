import unittest
from unittest.mock import Mock, patch

from open_jarvis.runtime import command_listener, readiness


class RuntimeFallbackTests(unittest.TestCase):
    def test_command_listener_reports_missing_microphone_without_raising(self):
        logs = []

        with patch("open_jarvis.runtime.command_listener.sr.Microphone", side_effect=OSError("no input device")):
            result = command_listener.listen_for_command(logger=Mock(), send_log=logs.append, speak=Mock())

        self.assertEqual(result, "")
        self.assertTrue(any("[ERROR] Microphone not detected" in item for item in logs))

    def test_emit_startup_readiness_logs_optional_missing_services(self):
        logs = []
        env = {
            "GROQ_API_KEY": "",
            "JARVIS_ENABLE_GROQ": "false",
            "SPOTIFY_CLIENT_ID": "",
            "SPOTIFY_CLIENT_SECRET": "",
            "JARVIS_ENABLE_SPOTIFY": "false",
        }

        report = readiness.emit_startup_readiness(
            env=env,
            send_log=logs.append,
            microphone_probe=lambda: False,
            recognition_mode=lambda: "online",
        )

        self.assertFalse(report["groq"])
        self.assertFalse(report["spotify"])
        self.assertFalse(report["microphone"])
        self.assertIn("[WARN] Groq API key not found. Running in local-only mode.", logs)
        self.assertIn("[WARN] Spotify credentials not found. Spotify integration disabled.", logs)
        self.assertIn("[ERROR] Microphone not detected.", logs)

    def test_emit_startup_readiness_uses_resolved_config_when_env_not_injected(self):
        logs = []
        resolved = {
            "GROQ_API_KEY": "",
            "JARVIS_ENABLE_GROQ": "false",
            "SPOTIFY_CLIENT_ID": "",
            "SPOTIFY_CLIENT_SECRET": "",
            "JARVIS_ENABLE_SPOTIFY": "false",
        }

        with patch("open_jarvis.runtime.readiness.resolved_env", return_value=resolved):
            report = readiness.emit_startup_readiness(
                send_log=logs.append,
                microphone_probe=lambda: True,
                recognition_mode=lambda: "online",
            )

        self.assertFalse(report["groq"])
        self.assertFalse(report["spotify"])
        self.assertTrue(report["microphone"])


if __name__ == "__main__":
    unittest.main()
