"""Domain-focused product tests split from the former monolithic product feature suite."""

from unittest import TestCase

from open_jarvis.audio.tts_provider import build_tts_provider_options, select_tts_provider
from open_jarvis.audio.voice_calibration import build_calibration_recommendation
from open_jarvis.integrations.offline_profile import build_offline_profile


class ProductAudioOfflineTest(TestCase):
    def test_tts_provider_selector_exposes_medium_roadmap_choice(self):
        options = build_tts_provider_options()
        selected = select_tts_provider({"JARVIS_TTS_PROVIDER": "edge"})

        self.assertIn("edge", [item["id"] for item in options])
        self.assertEqual(selected["id"], "edge")
        self.assertTrue(selected["available"])

    def test_offline_profile_covers_local_stt_tts_and_llm(self):
        profile = build_offline_profile(
            {"JARVIS_OFFLINE_STT": "1", "JARVIS_TTS_PROVIDER": "piper", "JARVIS_LOCAL_LLM_URL": "http://127.0.0.1:11434"}
        )

        self.assertEqual(profile["status"], "ready")
        self.assertEqual([item["id"] for item in profile["components"]], ["stt", "tts", "llm"])
        self.assertTrue(all(item["local"] for item in profile["components"]))

    def test_voice_calibration_recommends_threshold_from_noise_samples(self):
        recommendation = build_calibration_recommendation([120, 140, 160, 180], safety_margin=80)

        self.assertEqual(recommendation["status"], "ready")
        self.assertEqual(recommendation["recommended_threshold"], 230)
        self.assertIn("JARVIS_ENERGY_THRESHOLD=230", recommendation["env_line"])
