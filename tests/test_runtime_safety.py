import unittest
from unittest.mock import patch

from commands.domains.runtime_actions import handle_runtime_action
from runtime_safety import build_confirmation_prompt, is_destructive_action_allowed, requires_confirmation


class DummyLogger:
    def warning(self, *args):
        pass

    def exception(self, *args):
        pass


class RuntimeSafetyTests(unittest.TestCase):
    def test_destructive_actions_are_blocked_by_default(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("commands.domains.runtime_actions.run_command") as run_mock:
            result = handle_runtime_action("shutdown", {}, context)

        self.assertFalse(result)
        self.assertIn("blocked", spoken[0].lower())
        run_mock.assert_not_called()

    def test_destructive_actions_can_be_explicitly_enabled(self):
        with patch.dict("os.environ", {"JARVIS_ALLOW_DESTRUCTIVE_ACTIONS": "true"}):
            self.assertTrue(is_destructive_action_allowed())

    def test_confirmation_prompt_describes_risky_action(self):
        self.assertTrue(requires_confirmation("shutdown"))
        self.assertTrue(requires_confirmation("type_text"))
        self.assertFalse(requires_confirmation("get_time"))

        prompt = build_confirmation_prompt("shutdown", {"delay": 5})

        self.assertIn("sensitive action", prompt)
        self.assertIn("shutdown", prompt)
        self.assertIn("Approve or cancel", prompt)

    def test_cpu_check_uses_fast_configurable_interval(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with (
            patch.dict("os.environ", {"JARVIS_CPU_SAMPLE_INTERVAL": "0.05"}),
            patch("commands.domains.runtime_actions.psutil.cpu_percent", return_value=12) as cpu_mock,
        ):
            result = handle_runtime_action("get_cpu", {}, context)

        self.assertTrue(result)
        cpu_mock.assert_called_once_with(interval=0.05)
        self.assertIn("12", spoken[0])

    def test_runtime_delays_are_configurable(self):
        from commands.domains.runtime_actions import app_launch_delay, desktop_action_delay

        with patch.dict("os.environ", {"JARVIS_APP_LAUNCH_DELAY": "0", "JARVIS_SCREENSHOT_DELAY": "0.03"}):
            self.assertEqual(app_launch_delay(), 0)
            self.assertEqual(desktop_action_delay("JARVIS_SCREENSHOT_DELAY", 0.2), 0.03)


if __name__ == "__main__":
    unittest.main()
