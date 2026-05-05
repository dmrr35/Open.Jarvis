import unittest
from unittest.mock import patch

from open_jarvis.commands import groq_router


class DummyLogger:
    def __init__(self):
        self.messages = []

    def warning(self, message, *args):
        self.messages.append(("warning", message, args))

    def info(self, message, *args):
        self.messages.append(("info", message, args))

    def exception(self, message, *args):
        self.messages.append(("exception", message, args))


class GroqRouterTests(unittest.TestCase):
    def test_get_groq_model_prefers_environment_value(self):
        with patch.dict("os.environ", {"JARVIS_GROQ_MODEL": "llama-3.1-8b-instant"}):
            self.assertEqual(groq_router.get_groq_model(), "llama-3.1-8b-instant")

    def test_missing_client_returns_actionable_fallback(self):
        with patch.object(groq_router, "client", None):
            result = groq_router.analyze_with_groq("open chrome", client=None, logger=DummyLogger())

        self.assertEqual(result["action"], "talk")
        self.assertIn("Groq API key not found. Running in local-only mode.", result["response"])

    def test_groq_can_be_disabled_by_environment_flag(self):
        with patch.dict("os.environ", {"JARVIS_ENABLE_GROQ": "false"}):
            self.assertFalse(groq_router.groq_enabled())

    def test_summarize_text_truncates_long_input_before_request(self):
        captured = {}

        class DummyChat:
            def __init__(self):
                self.completions = self

            def create(self, **kwargs):
                captured["messages"] = kwargs["messages"]
                return type(
                    "Resp",
                    (),
                    {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "summary"})()})()]},
                )()

        class DummyClient:
            def __init__(self):
                self.chat = DummyChat()

        result = groq_router.summarize_text("x" * 5000, client=DummyClient(), logger=DummyLogger())

        self.assertEqual(result, "summary")
        self.assertLessEqual(len(captured["messages"][0]["content"]), 5000)
        self.assertIn("Summarize this in 3-4 sentences", captured["messages"][0]["content"])

    def test_extract_action_json_handles_text_around_json(self):
        result = groq_router.extract_action_json('Sure, sir.\n{"action": "talk", "params": {}, "response": "Ready."}')

        self.assertEqual(result["action"], "talk")

    def test_extract_action_json_handles_fenced_json(self):
        result = groq_router.extract_action_json('```json\n{"action": "talk", "params": {}}\n```')

        self.assertEqual(result["action"], "talk")


if __name__ == "__main__":
    unittest.main()
