from unittest import TestCase

from open_jarvis.audio.microphone import build_microphone_status, build_voice_calibration_status, microphone_available


class MicrophoneDegradedTest(TestCase):
    def test_microphone_available_uses_injected_probe(self):
        self.assertTrue(microphone_available(lambda: True))
        self.assertFalse(microphone_available(lambda: False))

    def test_microphone_probe_exception_returns_false(self):
        self.assertFalse(microphone_available(lambda: (_ for _ in ()).throw(OSError("no device"))))

    def test_status_reports_unavailable_without_raising(self):
        status = build_microphone_status(lambda: False)

        self.assertFalse(status["available"])
        self.assertEqual(status["status"], "unavailable")
        self.assertIn("Microphone unavailable", status["message"])

    def test_calibration_status_uses_existing_recommendation_logic(self):
        status = build_voice_calibration_status([100, 120, 140], safety_margin=80)

        self.assertEqual(status["status"], "ready")
        self.assertIn("JARVIS_ENERGY_THRESHOLD", status["env_line"])
