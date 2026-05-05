import unittest

from memory import DEFAULT_MEMORY
from memory_insights import build_memory_health_report, get_memory_quality_score, summarize_recent_activity


class MemoryInsightsTests(unittest.TestCase):
    def test_quality_score_rewards_preferences_and_activity(self):
        memory = {
            **DEFAULT_MEMORY,
            "preferences": {
                **DEFAULT_MEMORY["preferences"],
                "favorite_music": "Eminem",
                "favorite_app": "chrome",
                "preferred_volume": 70,
            },
            "notes": [{"text": "buy milk"}],
            "habits": {"open chrome": 4},
            "total_commands": 8,
        }

        self.assertGreaterEqual(get_memory_quality_score(memory), 59)

    def test_health_report_mentions_missing_preferences(self):
        report = build_memory_health_report({"preferences": {}, "notes": [], "habits": {}, "total_commands": 0})

        self.assertEqual(report["score"], 0)
        self.assertTrue(report["issues"])
        self.assertIn("Pruning", report["recommendation"])

    def test_recent_activity_falls_back_when_empty(self):
        self.assertEqual(summarize_recent_activity(limit=3, memory={"notes": [], "habits": {}}), "No recent memory activity yet.")


if __name__ == "__main__":
    unittest.main()
