from unittest import TestCase

from open_jarvis.audio.push_to_talk import PushToTalkController


class PushToTalkTest(TestCase):
    def test_push_to_talk_processes_command_without_wake_word(self):
        processed = []
        controller = PushToTalkController(microphone_probe=lambda: True, listen_for_command=lambda: "open chrome", process_command=processed.append)

        result = controller.start()

        self.assertEqual(result["status"], "processed")
        self.assertEqual(processed, ["open chrome"])

    def test_push_to_talk_reports_missing_microphone(self):
        controller = PushToTalkController(microphone_probe=lambda: False, listen_for_command=lambda: "open chrome", process_command=lambda command: None)

        result = controller.start()

        self.assertEqual(result["status"], "microphone_unavailable")

    def test_stop_marks_session_inactive(self):
        controller = PushToTalkController(microphone_probe=lambda: True, listen_for_command=lambda: "", process_command=lambda command: None)
        controller.active = True

        result = controller.stop()

        self.assertEqual(result["status"], "stopped")
        self.assertFalse(controller.active)
