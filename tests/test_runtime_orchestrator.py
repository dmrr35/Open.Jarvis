import unittest
from unittest.mock import Mock, patch

from open_jarvis.runtime.orchestrator import handle_runtime_command, should_return_to_standby


class DummyWakeState:
    def __init__(self):
        self.active = True


class RuntimeOrchestratorTest(unittest.TestCase):
    def test_handle_runtime_command_handles_shutdown_without_processing(self):
        logger = Mock()
        record_runtime_event = Mock()
        say_goodbye = Mock()
        maybe_tell_joke = Mock()
        handle_timer_command = Mock(return_value=False)
        process_command = Mock()
        wake_state = DummyWakeState()

        result = handle_runtime_command(
            "goodbye jarvis",
            logger=logger,
            process_command=process_command,
            handle_timer_command=handle_timer_command,
            say_goodbye=say_goodbye,
            maybe_tell_joke=maybe_tell_joke,
            record_runtime_event=record_runtime_event,
            wake_state=wake_state,
        )

        self.assertFalse(result)
        say_goodbye.assert_called_once()
        process_command.assert_not_called()
        maybe_tell_joke.assert_not_called()
        record_runtime_event.assert_called_once()

    def test_handle_runtime_command_updates_wake_state_for_timer(self):
        logger = Mock()
        record_runtime_event = Mock()
        say_goodbye = Mock()
        maybe_tell_joke = Mock()
        handle_timer_command = Mock(return_value=True)
        process_command = Mock()
        wake_state = DummyWakeState()

        result = handle_runtime_command(
            "set a timer for 10 minutes",
            logger=logger,
            process_command=process_command,
            handle_timer_command=handle_timer_command,
            say_goodbye=say_goodbye,
            maybe_tell_joke=maybe_tell_joke,
            record_runtime_event=record_runtime_event,
            wake_state=wake_state,
        )

        self.assertTrue(result)
        self.assertFalse(wake_state.active)
        handle_timer_command.assert_called_once()
        process_command.assert_not_called()
        maybe_tell_joke.assert_not_called()

    def test_should_return_to_standby_respects_timeout(self):
        with patch("open_jarvis.runtime.orchestrator.time.time", return_value=12.0):
            self.assertFalse(should_return_to_standby(10.0, 5))
        with patch("open_jarvis.runtime.orchestrator.time.time", return_value=1.0):
            self.assertTrue(should_return_to_standby(0.0, 0))


if __name__ == "__main__":
    unittest.main()
