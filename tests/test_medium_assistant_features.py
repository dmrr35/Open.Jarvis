import unittest
from unittest.mock import patch

from open_jarvis.commands import groq_router
from open_jarvis.commands.domains.memory_actions import handle_memory_action
from open_jarvis.commands.domains.runtime_actions import handle_runtime_action


class DummyLogger:
    def __init__(self):
        self.messages = []

    def warning(self, message, *args):
        self.messages.append(("warning", message % args if args else message))

    def info(self, message, *args):
        self.messages.append(("info", message % args if args else message))

    def exception(self, message, *args):
        self.messages.append(("exception", message % args if args else message))


class MediumAssistantFeaturesTests(unittest.TestCase):
    def test_groq_rate_limit_activates_cooldown_fallback(self):
        class RateLimitedCompletions:
            def create(self, **kwargs):
                raise groq_router.GroqError("rate limit exceeded")

        class DummyClient:
            chat = type("Chat", (), {"completions": RateLimitedCompletions()})()

        with (
            patch("open_jarvis.commands.groq_router.is_groq_cooling_down", return_value=False),
            patch("open_jarvis.commands.groq_router.activate_groq_cooldown") as cooldown_mock,
        ):
            result = groq_router.analyze_with_groq("open chrome", client=DummyClient(), logger=DummyLogger())

        self.assertEqual(result["action"], "talk")
        self.assertIn("free Groq quota", result["response"])
        cooldown_mock.assert_called_once()

    def test_summarize_clipboard_uses_local_fallback_when_cloud_summary_missing(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger(), "summarize_text": lambda text: None}
        text = "First sentence is useful. Second sentence has detail. Third sentence is extra."

        with patch("open_jarvis.commands.domains.runtime_actions.pyperclip.paste", return_value=text):
            result = handle_runtime_action("summarize_clipboard", {}, context)

        self.assertTrue(result)
        self.assertIn("First sentence is useful", spoken[0])
        self.assertNotIn("trouble summarizing", spoken[0])

    def test_daily_summary_combines_memory_and_system_context(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with (
            patch("open_jarvis.commands.domains.memory_actions.get_stats", return_value={"total_commands": 8, "notes_count": 2, "habits_count": 1}),
            patch("open_jarvis.commands.domains.memory_actions.summarize_recent_activity", return_value="Recent activity summary."),
        ):
            result = handle_memory_action("daily_summary", {}, context)

        self.assertTrue(result)
        self.assertIn("Daily summary", spoken[0])
        self.assertIn("8 commands", spoken[0])
        self.assertIn("Recent activity summary", spoken[0])


if __name__ == "__main__":
    unittest.main()
