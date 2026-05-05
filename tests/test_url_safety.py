import unittest
from unittest.mock import patch

from open_jarvis.commands.domains.runtime_actions import handle_runtime_action
from open_jarvis.integrations.url_safety import normalize_web_url


class DummyLogger:
    def warning(self, *args):
        pass

    def exception(self, *args):
        pass


class UrlSafetyTests(unittest.TestCase):
    def test_normalize_web_url_accepts_http_and_https(self):
        self.assertEqual(normalize_web_url("example.com"), "https://example.com")
        self.assertEqual(normalize_web_url("http://example.com"), "http://example.com")

    def test_normalize_web_url_rejects_unsafe_schemes(self):
        self.assertIsNone(normalize_web_url("javascript:alert(1)"))
        self.assertIsNone(normalize_web_url("file:///C:/Windows/System32"))

    def test_open_web_blocks_unsafe_url(self):
        spoken = []
        context = {"speak": spoken.append, "logger": DummyLogger()}

        with patch("open_jarvis.commands.domains.runtime_actions.webbrowser.open") as open_mock:
            result = handle_runtime_action("open_web", {"url": "javascript:alert(1)"}, context)

        self.assertFalse(result)
        self.assertIn("blocked", spoken[0].lower())
        open_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
