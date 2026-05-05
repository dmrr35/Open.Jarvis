import unittest
from unittest.mock import patch

import open_jarvis.runtime.jarvis_runtime as jarvis_runtime
from open_jarvis.runtime import timer as timer_runtime


class JarvisRuntimeTest(unittest.TestCase):
    def test_parse_duration_supports_hours_minutes_seconds(self):
        self.assertEqual(jarvis_runtime.parse_duration("set a timer for 1 hour 2 minutes 3 seconds"), 3723)

    def test_handle_timer_command_starts_timer(self):
        spoken = []

        with patch("open_jarvis.runtime.jarvis_runtime.speak", side_effect=spoken.append), patch("open_jarvis.runtime.timer.start_timer") as start_timer_mock:
            result = jarvis_runtime.handle_timer_command("set a timer for 10 minutes")

        self.assertTrue(result)
        self.assertTrue(spoken[0].startswith("Timer set for"))
        start_timer_mock.assert_called_once()

    def test_handle_timer_command_returns_false_for_non_timer_text(self):
        self.assertFalse(jarvis_runtime.handle_timer_command("open chrome"))

    def test_runtime_timer_parse_duration_matches_wrapper(self):
        self.assertEqual(timer_runtime.parse_duration("1 hour 5 minutes"), jarvis_runtime.parse_duration("1 hour 5 minutes"))


if __name__ == "__main__":
    unittest.main()
