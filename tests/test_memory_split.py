import unittest
from unittest.mock import patch

import open_jarvis.memory.memory_habits as memory_habits
import open_jarvis.memory.memory_notes as memory_notes
import open_jarvis.memory.memory_preferences as memory_preferences
import open_jarvis.memory.memory_short_term as memory_short_term


class MemorySplitTests(unittest.TestCase):
    def tearDown(self):
        memory_short_term.clear_short_term()

    def test_short_term_round_trip(self):
        memory_short_term.add_to_short_term("user", "hello")
        self.assertEqual(memory_short_term.get_short_term()[0]["content"], "hello")
        self.assertEqual(memory_short_term.get_short_term_for_groq()[0]["role"], "user")

    def test_track_command_updates_top_habits(self):
        memory = {"habits": {}, "total_commands": 0, "preferences": {}, "notes": []}
        with patch("open_jarvis.memory.memory_habits.load_memory", return_value=memory), patch("open_jarvis.memory.memory_habits.save_memory") as save_mock:
            memory_habits.track_command("open chrome")

        save_mock.assert_called_once()

    def test_preferences_and_notes_are_routed(self):
        with patch("open_jarvis.memory.memory_preferences.set_preference") as set_pref:
            result = memory_preferences.detect_and_save_preference("always open chrome")
        self.assertIn("chrome", result)
        set_pref.assert_called_with("favorite_app", "chrome")

        with patch("open_jarvis.memory.memory_notes.load_memory", return_value={"notes": []}), patch("open_jarvis.memory.memory_notes.save_memory") as save_mock:
            memory_notes.add_note("buy milk")
        save_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
