import unittest

from commands.local_intent_router import normalize_command, route_local_intent


class LocalIntentRouterTests(unittest.TestCase):
    def test_normalize_command_handles_case_and_spacing(self):
        self.assertEqual(normalize_command("  OPEN   CHROME   "), "open chrome")

    def test_routes_system_status_commands_without_llm(self):
        cases = {
            "what time is it": "get_time",
            "what date is it": "get_date",
            "cpu usage": "get_cpu",
            "memory usage": "get_ram",
            "battery status": "get_battery",
        }

        for command, action in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertIsNotNone(result)
                self.assertEqual(result["action"], action)

    def test_routes_desktop_utility_commands_without_llm(self):
        cases = {
            "take screenshot": "screenshot",
            "read clipboard": "read_clipboard",
            "summarize clipboard": "summarize_clipboard",
            "read notes": "read_notes",
            "memory stats": "memory_stats",
            "memory habits": "memory_habits",
            "clean memory": "prune_memory",
            "daily summary": "daily_summary",
        }

        for command, action in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertIsNotNone(result)
                self.assertEqual(result["action"], action)

    def test_routes_open_app_with_supported_application(self):
        result = route_local_intent("open chrome")

        self.assertEqual(result["action"], "open_app")
        self.assertEqual(result["params"], {"app": "chrome"})

    def test_routes_google_search_and_extracts_query(self):
        result = route_local_intent("google open source AI architecture")

        self.assertEqual(result["action"], "search_google")
        self.assertEqual(result["params"], {"query": "open source ai architecture"})

    def test_routes_general_search_phrases_and_extracts_query(self):
        cases = {
            "search for python desktop assistant": "python desktop assistant",
            "look up groq free api": "groq free api",
            "find jarvis ui inspiration": "jarvis ui inspiration",
        }

        for command, query in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], "search_google")
                self.assertEqual(result["params"], {"query": query})

    def test_routes_open_web_for_known_sites_and_urls(self):
        cases = {
            "open youtube": "https://www.youtube.com",
            "open github": "https://github.com",
            "open https://example.com/docs": "https://example.com/docs",
            "go to openai.com": "https://openai.com",
        }

        for command, url in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], "open_web")
                self.assertEqual(result["params"], {"url": url})

    def test_routes_window_and_volume_controls_without_llm(self):
        cases = {
            "minimize all windows": ("minimize_all", {}),
            "maximize window": ("maximize_window", {}),
            "close current window": ("close_window", {}),
            "mute volume": ("press_key", {"key": "volumemute"}),
            "volume up": ("press_key", {"key": "volumeup"}),
            "turn volume down": ("press_key", {"key": "volumedown"}),
        }

        for command, expected in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual((result["action"], result["params"]), expected)

    def test_routes_spotify_controls_without_llm(self):
        cases = {
            "play music": "spotify_play",
            "pause music": "spotify_pause",
            "next track": "spotify_next",
            "previous song": "spotify_prev",
            "what is playing on spotify": "spotify_current",
        }

        for command, action in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], action)

    def test_routes_add_note_and_extracts_note_text(self):
        result = route_local_intent("add note run tests tomorrow")

        self.assertEqual(result["action"], "add_note")
        self.assertEqual(result["params"], {"text": "run tests tomorrow"})

    def test_returns_none_for_complex_commands_that_need_llm(self):
        self.assertIsNone(route_local_intent("open YouTube, start lo-fi, and then start focus mode"))


if __name__ == "__main__":
    unittest.main()
