import unittest
from unittest.mock import patch

import komutlar


class ProcessCommandLocalRouterTests(unittest.TestCase):
    def test_process_command_executes_local_action_before_groq(self):
        with (
            patch("komutlar.add_to_short_term"),
            patch("komutlar.track_command"),
            patch("komutlar.detect_and_save_preference", return_value=None),
            patch("komutlar.route_local_intent", return_value={"action": "get_time", "params": {}, "response": ""}) as local_mock,
            patch("komutlar.analyze_with_groq") as groq_mock,
            patch("komutlar.execute_action", return_value=True) as execute_mock,
        ):
            result = komutlar.process_command("what time is it")

        self.assertTrue(result)
        local_mock.assert_called_once_with("what time is it")
        groq_mock.assert_not_called()
        execute_mock.assert_called_once_with({"action": "get_time", "params": {}, "response": ""})

    def test_process_command_falls_back_to_groq_when_local_router_has_no_match(self):
        groq_action = {"action": "talk", "params": {}, "response": "At once, sir."}

        with (
            patch("komutlar.add_to_short_term"),
            patch("komutlar.track_command"),
            patch("komutlar.detect_and_save_preference", return_value=None),
            patch("komutlar.route_local_intent", return_value=None),
            patch("komutlar.analyze_with_groq", return_value=groq_action) as groq_mock,
            patch("komutlar.execute_action", return_value=True) as execute_mock,
        ):
            result = komutlar.process_command("please plan my morning")

        self.assertTrue(result)
        groq_mock.assert_called_once_with("please plan my morning")
        execute_mock.assert_called_once_with(groq_action)

    def test_process_command_routes_expanded_daily_commands_locally(self):
        commands = [
            "open youtube",
            "search for python desktop assistant",
            "volume up",
            "pause music",
            "clean memory",
        ]

        for command in commands:
            with self.subTest(command=command):
                with (
                    patch("komutlar.add_to_short_term"),
                    patch("komutlar.track_command"),
                    patch("komutlar.detect_and_save_preference", return_value=None),
                    patch("komutlar.analyze_with_groq") as groq_mock,
                    patch("komutlar.execute_action", return_value=True) as execute_mock,
                ):
                    result = komutlar.process_command(command)

                self.assertTrue(result)
                groq_mock.assert_not_called()
                execute_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
