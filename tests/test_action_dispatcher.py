import unittest
from unittest.mock import patch

from commands.action_dispatcher import execute_action
from commands.domains.memory_actions import handle_memory_action
from commands.domains.runtime_actions import env_float, handle_runtime_action


class DummyLogger:
    def __init__(self):
        self.messages = []

    def warning(self, message, *args):
        self.messages.append(("warning", message % args if args else message))

    def info(self, message, *args):
        self.messages.append(("info", message % args if args else message))

    def exception(self, message, *args):
        self.messages.append(("exception", message % args if args else message))


class ActionDispatcherTest(unittest.TestCase):
    def test_execute_action_routes_and_speaks_response(self):
        spoken = []
        context = {
            "speak": spoken.append,
            "logger": DummyLogger(),
            "summarize_text": lambda text: "summary",
        }

        with patch("commands.action_dispatcher.execute_single_action", return_value=True) as single_mock:
            result = execute_action(
                {"action": "get_time", "params": {}, "response": "Opening time, sir."},
                context,
            )

        self.assertTrue(result)
        self.assertEqual(spoken[0], "Opening time, sir.")
        single_mock.assert_called_once()

    def test_multi_action_delay_is_configurable(self):
        context = {"speak": lambda text: None, "logger": DummyLogger()}

        with (
            patch.dict("os.environ", {"JARVIS_ACTION_SEQUENCE_DELAY": "0"}),
            patch("commands.action_dispatcher.execute_single_action", return_value=True),
            patch("commands.action_dispatcher.time.sleep") as sleep_mock,
        ):
            result = execute_action({"actions": [{"action": "get_time"}, {"action": "get_date"}]}, context)

        self.assertTrue(result)
        sleep_mock.assert_not_called()

    def test_execute_action_rejects_malformed_sub_action_without_crashing(self):
        spoken = []
        logger = DummyLogger()
        context = {"speak": spoken.append, "logger": logger}

        result = execute_action({"actions": [{"params": {}}]}, context)

        self.assertFalse(result)
        self.assertIn("malformed", spoken[0].lower())
        self.assertTrue(any("Malformed" in message for _, message in logger.messages))

    def test_execute_action_rejects_invalid_payload_schema(self):
        spoken = []
        logger = DummyLogger()
        context = {"speak": spoken.append, "logger": logger}

        result = execute_action({"action": "get_time", "params": []}, context)

        self.assertFalse(result)
        self.assertIn("invalid action payload", spoken[0].lower())
        self.assertTrue(any("Invalid action payload" in message for _, message in logger.messages))

    def test_runtime_handler_opens_web(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger(), "summarize_text": lambda text: "summary"}

        with patch("commands.domains.runtime_actions.webbrowser.open") as open_mock:
            result = handle_runtime_action("open_web", {"url": "https://example.com"}, context)

        self.assertTrue(result)
        open_mock.assert_called_once_with("https://example.com")

    def test_runtime_helpers_handle_invalid_env_and_launch_known_app(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch.dict("os.environ", {"JARVIS_BAD_FLOAT": "not-a-number"}):
            self.assertEqual(env_float("JARVIS_BAD_FLOAT", 0.5), 0.5)

        with (
            patch("commands.domains.runtime_actions.os.path.exists", return_value=True),
            patch("commands.domains.runtime_actions.launch_process") as launch_mock,
            patch("commands.domains.runtime_actions.record_runtime_event") as event_mock,
            patch("commands.domains.runtime_actions.time.sleep"),
            patch.dict("os.environ", {"JARVIS_APP_LAUNCH_DELAY": "0"}),
        ):
            result = handle_runtime_action("open_app", {"app": "notepad"}, context)

        self.assertTrue(result)
        launch_mock.assert_called_once()
        event_mock.assert_called_once()

    def test_runtime_handler_launches_app_from_system_path_fallback(self):
        context = {"speak": lambda text: None, "logger": DummyLogger()}

        with (
            patch("commands.domains.runtime_actions.os.path.exists", return_value=False),
            patch("commands.domains.runtime_actions.launch_process") as launch_mock,
            patch("commands.domains.runtime_actions.record_runtime_event") as event_mock,
            patch("commands.domains.runtime_actions.time.sleep"),
            patch.dict("os.environ", {"JARVIS_APP_LAUNCH_DELAY": "0"}),
        ):
            result = handle_runtime_action("open_app", {"app": "calc"}, context)

        self.assertTrue(result)
        launch_mock.assert_called_once_with(["calc"])
        event_mock.assert_called_once()

    def test_runtime_handler_blocks_unsafe_web_url(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("commands.domains.runtime_actions.webbrowser.open") as open_mock:
            result = handle_runtime_action("open_web", {"url": "file:///secret"}, context)

        self.assertFalse(result)
        open_mock.assert_not_called()
        self.assertIn("blocked", spoken[0].lower())

    def test_runtime_handler_blocks_destructive_actions_without_permission(self):
        spoken = []
        logger = DummyLogger()
        context = {"speak": spoken.append, "logger": logger}

        with (
            patch("commands.domains.runtime_actions.run_command") as run_mock,
            patch("commands.domains.runtime_actions.record_runtime_event") as event_mock,
            patch("commands.domains.runtime_actions.is_destructive_action_allowed", return_value=False),
        ):
            result = handle_runtime_action("shutdown", {}, context)

        self.assertFalse(result)
        run_mock.assert_not_called()
        event_mock.assert_called_once()
        self.assertIn("blocked", spoken[0].lower())

    def test_runtime_handler_searches_google(self):
        context = {"speak": lambda text: None, "logger": DummyLogger()}

        with patch("commands.domains.runtime_actions.webbrowser.open") as open_mock:
            result = handle_runtime_action("search_google", {"query": "jarvis runtime coverage"}, context)

        self.assertTrue(result)
        opened_url = open_mock.call_args.args[0]
        self.assertIn("google", opened_url)
        self.assertIn("jarvis", opened_url)

    def test_runtime_handler_reports_time_and_date(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        self.assertTrue(handle_runtime_action("get_time", {}, context))
        self.assertTrue(handle_runtime_action("get_date", {}, context))

        self.assertIn("current time", spoken[0])
        self.assertIn("Today is", spoken[1])

    def test_runtime_handler_reports_missing_battery(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("commands.domains.runtime_actions.psutil.sensors_battery", return_value=None):
            result = handle_runtime_action("get_battery", {}, context)

        self.assertTrue(result)
        self.assertIn("No battery", spoken[0])

    def test_runtime_handler_reads_empty_clipboard(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("commands.domains.runtime_actions.pyperclip.paste", return_value=""):
            result = handle_runtime_action("read_clipboard", {}, context)

        self.assertTrue(result)
        self.assertIn("empty", spoken[0].lower())

    def test_runtime_handler_truncates_long_clipboard_text(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("commands.domains.runtime_actions.pyperclip.paste", return_value="x" * 900):
            result = handle_runtime_action("read_clipboard", {}, context)

        self.assertTrue(result)
        self.assertIn("quite long", spoken[0])
        self.assertEqual(len(spoken[1]), 800)

    def test_runtime_handler_summarizes_clipboard_with_context_callback(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger(), "summarize_text": lambda text: f"summary:{text}"}

        with patch("commands.domains.runtime_actions.pyperclip.paste", return_value="long text"):
            result = handle_runtime_action("summarize_clipboard", {}, context)

        self.assertTrue(result)
        self.assertEqual(spoken[0], "summary:long text")

    def test_runtime_handler_summarize_clipboard_empty_and_local_fallback_summary(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger(), "summarize_text": lambda text: None}

        with patch("commands.domains.runtime_actions.pyperclip.paste", side_effect=["", "important text"]):
            self.assertTrue(handle_runtime_action("summarize_clipboard", {}, context))
            self.assertTrue(handle_runtime_action("summarize_clipboard", {}, context))

        self.assertIn("empty", spoken[0].lower())
        self.assertIn("important text", spoken[1])

    def test_runtime_handler_keyboard_and_mouse_actions(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with (
            patch("commands.domains.runtime_actions.time.sleep"),
            patch("commands.domains.runtime_actions.pyautogui.typewrite") as typewrite_mock,
            patch("commands.domains.runtime_actions.pyautogui.hotkey") as hotkey_mock,
            patch("commands.domains.runtime_actions.pyautogui.click") as click_mock,
            patch("commands.domains.runtime_actions.pyautogui.scroll") as scroll_mock,
        ):
            self.assertTrue(handle_runtime_action("type_text", {"text": "hello"}, context))
            self.assertTrue(handle_runtime_action("press_key", {"key": "ctrl+c"}, context))
            self.assertTrue(handle_runtime_action("mouse_click", {"x": 1, "y": 2}, context))
            self.assertTrue(handle_runtime_action("scroll", {"direction": "down", "amount": 4}, context))

        typewrite_mock.assert_called_once()
        hotkey_mock.assert_called_once_with("ctrl", "c")
        click_mock.assert_called_once()
        scroll_mock.assert_called_once_with(-4)

    def test_runtime_handler_keyboard_mouse_and_scroll_edge_paths(self):
        context = {"speak": lambda text: None, "logger": DummyLogger()}

        with (
            patch("commands.domains.runtime_actions.time.sleep"),
            patch("commands.domains.runtime_actions.pyautogui.typewrite") as typewrite_mock,
            patch("commands.domains.runtime_actions.pyautogui.press") as press_mock,
            patch("commands.domains.runtime_actions.pyautogui.doubleClick") as double_mock,
            patch("commands.domains.runtime_actions.pyautogui.scroll") as scroll_mock,
        ):
            self.assertTrue(handle_runtime_action("type_text", {}, context))
            self.assertTrue(handle_runtime_action("press_key", {"key": "enter"}, context))
            self.assertTrue(handle_runtime_action("mouse_click", {"x": 5, "y": 6, "button": "double"}, context))
            self.assertTrue(handle_runtime_action("scroll", {"direction": "up", "amount": 7}, context))

        typewrite_mock.assert_not_called()
        press_mock.assert_called_once_with("enter")
        double_mock.assert_called_once_with(5, 6)
        scroll_mock.assert_called_once_with(7)

    def test_runtime_handler_covers_system_metrics_and_desktop_controls(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        class Battery:
            percent = 87
            power_plugged = True

        class Memory:
            percent = 42
            used = 4 * 1024**3
            total = 16 * 1024**3

        with (
            patch("commands.domains.runtime_actions.psutil.sensors_battery", return_value=Battery()),
            patch("commands.domains.runtime_actions.psutil.virtual_memory", return_value=Memory()),
            patch("commands.domains.runtime_actions.psutil.cpu_percent", return_value=12.5),
            patch("commands.domains.runtime_actions.pyautogui.hotkey") as hotkey_mock,
            patch("commands.domains.runtime_actions.run_command") as run_mock,
            patch("commands.domains.runtime_actions.is_destructive_action_allowed", return_value=True),
            patch("commands.domains.runtime_actions.time.sleep"),
            patch.dict("os.environ", {"JARVIS_CPU_SAMPLE_INTERVAL": "0"}),
        ):
            self.assertTrue(handle_runtime_action("get_battery", {}, context))
            self.assertTrue(handle_runtime_action("get_ram", {}, context))
            self.assertTrue(handle_runtime_action("get_cpu", {}, context))
            self.assertTrue(handle_runtime_action("minimize_all", {}, context))
            self.assertTrue(handle_runtime_action("maximize_window", {}, context))
            self.assertTrue(handle_runtime_action("close_window", {}, context))
            self.assertTrue(handle_runtime_action("lock_screen", {}, context))

        self.assertIn("87 percent", spoken[0])
        self.assertIn("Memory usage", spoken[1])
        self.assertIn("12.5 percent", spoken[2])
        self.assertEqual(hotkey_mock.call_count, 3)
        run_mock.assert_called_once()

    def test_runtime_handler_screenshot_and_clipboard_error_paths_are_safe(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger(), "summarize_text": lambda text: None}

        class Screenshot:
            def save(self, path):
                self.path = path

        with (
            patch("commands.domains.runtime_actions.os.makedirs") as makedirs_mock,
            patch("commands.domains.runtime_actions.pyautogui.screenshot", return_value=Screenshot()),
            patch("commands.domains.runtime_actions.launch_process") as launch_mock,
            patch("commands.domains.runtime_actions.time.sleep"),
            patch("commands.domains.runtime_actions.pyperclip.paste", side_effect=RuntimeError("clipboard locked")),
            patch.dict("os.environ", {"USERPROFILE": "C:\\Users\\W10"}),
        ):
            self.assertTrue(handle_runtime_action("screenshot", {}, context))
            self.assertTrue(handle_runtime_action("read_clipboard", {}, context))
            self.assertTrue(handle_runtime_action("summarize_clipboard", {}, context))

        makedirs_mock.assert_called_once()
        launch_mock.assert_called_once()
        self.assertTrue(any("Screenshot saved" in item for item in spoken))
        self.assertTrue(any("couldn't read" in item.lower() for item in spoken))
        self.assertTrue(any("couldn't access" in item.lower() for item in spoken))

    def test_runtime_handler_launch_app_failure_and_unknown_action(self):
        spoken = []
        logger = DummyLogger()
        context = {"speak": spoken.append, "logger": logger}

        with (
            patch("commands.domains.runtime_actions.os.path.exists", return_value=False),
            patch("commands.domains.runtime_actions.launch_process", side_effect=OSError("missing")),
        ):
            result = handle_runtime_action("open_app", {"app": "missing_app"}, context)

        self.assertTrue(result)
        self.assertIn("couldn't locate", spoken[0])
        self.assertEqual(handle_runtime_action("unknown_action", {}, context), None)

    def test_runtime_handler_power_actions_when_explicitly_allowed(self):
        context = {"speak": lambda text: None, "logger": DummyLogger()}

        with (
            patch("commands.domains.runtime_actions.is_destructive_action_allowed", return_value=True),
            patch("commands.domains.runtime_actions.run_command") as run_mock,
            patch("commands.domains.runtime_actions.time.sleep") as sleep_mock,
            patch.dict("os.environ", {"JARVIS_SLEEP_ACTION_DELAY": "0"}),
        ):
            self.assertTrue(handle_runtime_action("sleep", {}, context))
            self.assertFalse(handle_runtime_action("shutdown", {}, context))
            self.assertFalse(handle_runtime_action("restart", {}, context))

        sleep_mock.assert_not_called()
        self.assertEqual(run_mock.call_count, 3)

    def test_runtime_handler_sleep_honors_configured_delay(self):
        context = {"speak": lambda text: None, "logger": DummyLogger()}

        with (
            patch("commands.domains.runtime_actions.is_destructive_action_allowed", return_value=True),
            patch("commands.domains.runtime_actions.run_command"),
            patch("commands.domains.runtime_actions.time.sleep") as sleep_mock,
            patch.dict("os.environ", {"JARVIS_SLEEP_ACTION_DELAY": "0.25"}),
        ):
            self.assertTrue(handle_runtime_action("sleep", {}, context))

        sleep_mock.assert_called_once_with(0.25)

    def test_memory_handler_reads_notes(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("commands.domains.memory_actions.get_notes", return_value=[{"text": "alpha"}, {"text": "beta"}]):
            result = handle_memory_action("read_notes", {}, context)

        self.assertTrue(result)
        self.assertIn("2 notes", spoken[0])
        self.assertIn("alpha", spoken[1])

    def test_memory_handler_reports_stats(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("commands.domains.memory_actions.get_stats") as stats_mock:
            stats_mock.return_value = {"total_commands": 7, "notes_count": 2, "habits_count": 1}
            result = handle_memory_action("memory_stats", {}, context)

        self.assertTrue(result)
        self.assertIn("7 commands", spoken[0])
        self.assertIn("2 notes", spoken[0])

    def test_memory_handler_covers_habits_health_summary_prune_and_empty_note(self):
        spoken = []
        logger = DummyLogger()
        context = {"speak": spoken.append, "logger": logger}

        with (
            patch("commands.domains.memory_actions.get_top_habits", side_effect=[[("open chrome", 3)], []]),
            patch("commands.domains.memory_actions.build_memory_health_report", return_value={"score": 82, "recommendation": "Healthy."}),
            patch("commands.domains.memory_actions.summarize_recent_activity", return_value="Recent activity summary."),
            patch("commands.domains.memory_actions.prune_memory", return_value={"notes": [1, 2], "habits": {"open": 1}}),
            patch("commands.domains.memory_actions.add_note") as add_note_mock,
            patch("commands.domains.memory_actions.get_notes", return_value=[]),
        ):
            self.assertTrue(handle_memory_action("memory_habits", {}, context))
            self.assertTrue(handle_memory_action("memory_habits", {}, context))
            self.assertTrue(handle_memory_action("memory_health", {}, context))
            self.assertTrue(handle_memory_action("memory_summary", {}, context))
            self.assertTrue(handle_memory_action("prune_memory", {}, context))
            self.assertTrue(handle_memory_action("add_note", {}, context))
            self.assertTrue(handle_memory_action("read_notes", {}, context))

        add_note_mock.assert_not_called()
        self.assertTrue(any("most used commands" in item for item in spoken))
        self.assertTrue(any("haven't learned" in item for item in spoken))
        self.assertTrue(any("Memory health is 82" in item for item in spoken))
        self.assertTrue(any("What would you like" in item for item in spoken))
        self.assertTrue(any("no saved notes" in item for item in spoken))
        self.assertTrue(any(level == "info" for level, _ in logger.messages))

    def test_memory_handler_respects_privacy_mode_for_note_writes(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger(), "privacy_mode": True}

        with patch("commands.domains.memory_actions.add_note") as add_note_mock:
            result = handle_memory_action("add_note", {"text": "secret"}, context)

        self.assertTrue(result)
        add_note_mock.assert_not_called()
        self.assertIn("privacy mode", spoken[0].lower())

    def test_memory_handler_add_note_and_unknown_action(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("commands.domains.memory_actions.add_note") as add_note_mock:
            self.assertTrue(handle_memory_action("add_note", {"text": "ship runtime package"}, context))
            self.assertIsNone(handle_memory_action("unknown_memory_action", {}, context))

        add_note_mock.assert_called_once_with("ship runtime package")
        self.assertIn("Note saved", spoken[0])


if __name__ == "__main__":
    unittest.main()
