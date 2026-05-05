import unittest
from unittest.mock import patch

from runtime import voice_personality


class DummyLogger:
    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None


class VoicePersonalityTest(unittest.TestCase):
    def test_greet_routes_morning_message(self):
        spoken = []

        with patch("runtime.voice_personality.datetime.datetime") as dt:
            dt.now.return_value.hour = 9
            voice_personality.greet(speak=spoken.append, send_log=spoken.append)

        self.assertTrue(any("Good morning" in item for item in spoken))

    def test_safe_speak_reports_tts_failure_without_raising(self):
        logs = []

        result = voice_personality.safe_speak(
            "Good day, sir.",
            speak=lambda _text: (_ for _ in ()).throw(RuntimeError("audio device unavailable")),
            send_log=logs.append,
            logger=DummyLogger(),
        )

        self.assertFalse(result)
        self.assertIn("Voice output failed", logs[0])

    def test_say_goodbye_uses_goodbye_pool(self):
        spoken = []

        with (
            patch("runtime.voice_personality.datetime.datetime") as dt,
            patch("runtime.voice_personality.random.choice", return_value="Farewell, sir."),
        ):
            dt.now.return_value.hour = 14
            voice_personality.say_goodbye(speak=spoken.append)

        self.assertEqual(spoken[0], "Farewell, sir.")

    def test_say_goodbye_reports_tts_failure_without_raising(self):
        logs = []

        with patch("runtime.voice_personality.random.choice", return_value="Farewell, sir."):
            voice_personality.say_goodbye(
                speak=lambda _text: (_ for _ in ()).throw(RuntimeError("audio offline")),
                send_log=logs.append,
                logger=DummyLogger(),
            )

        self.assertIn("Voice output failed", logs[0])

    def test_maybe_tell_joke_updates_state(self):
        spoken = []
        state = {"command_count": 4, "joke_interval": 5}

        with (
            patch("runtime.voice_personality.random.randint", return_value=6),
            patch("runtime.voice_personality.random.choice", return_value="A joke, sir."),
        ):
            voice_personality.maybe_tell_joke(speak=spoken.append, send_log=spoken.append, logger=DummyLogger(), state=state)

        self.assertEqual(state["command_count"], 0)
        self.assertEqual(state["joke_interval"], 6)
        self.assertEqual(spoken[-1], "JARVIS: A joke, sir.")

    def test_maybe_tell_joke_reports_tts_failure_without_raising(self):
        logs = []
        state = {"command_count": 4, "joke_interval": 5}

        with (
            patch("runtime.voice_personality.random.randint", return_value=6),
            patch("runtime.voice_personality.random.choice", return_value="A joke, sir."),
        ):
            voice_personality.maybe_tell_joke(
                speak=lambda _text: (_ for _ in ()).throw(RuntimeError("audio offline")),
                send_log=logs.append,
                logger=DummyLogger(),
                state=state,
            )

        self.assertIn("Voice output failed", logs[0])


if __name__ == "__main__":
    unittest.main()
