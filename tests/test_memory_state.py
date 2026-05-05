import unittest
from unittest.mock import patch

import memory_preferences
import memory_state


class MemoryStateTests(unittest.TestCase):
    def tearDown(self):
        memory_state.clear_short_term()

    def test_short_term_add_and_clear(self):
        memory_state.add_to_short_term("user", "hello")
        self.assertEqual(len(memory_state.get_short_term()), 1)
        self.assertEqual(memory_state.get_short_term_for_groq()[0]["role"], "user")

        memory_state.clear_short_term()
        self.assertEqual(memory_state.get_short_term(), [])

    def test_detect_and_save_preference_routes_music_and_volume(self):
        with patch("memory_preferences.set_preference") as set_preference:
            response = memory_state.detect_and_save_preference("always play eminem")

        self.assertIn("eminem", response.lower())
        set_preference.assert_called_with("favorite_music", "eminem")

        with patch("memory_preferences.set_preference") as set_preference:
            response = memory_state.detect_and_save_preference("set volume to 70 by default")

        self.assertIn("70", response)
        set_preference.assert_called_with("preferred_volume", 70)

    def test_memory_state_reexports_split_modules(self):
        self.assertIs(memory_state.add_to_short_term, __import__("memory_short_term").add_to_short_term)
        self.assertIs(memory_state.set_preference, memory_preferences.set_preference)


if __name__ == "__main__":
    unittest.main()
