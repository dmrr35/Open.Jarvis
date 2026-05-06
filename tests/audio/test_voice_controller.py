from unittest import TestCase

from open_jarvis.audio.tts_queue import TTSQueue
from open_jarvis.audio.voice_controller import VoiceController
from open_jarvis.audio.voice_state import VoiceState


class VoiceControllerTest(TestCase):
    def test_controller_processes_wake_command_and_response(self):
        processed = []
        spoken = []
        controller = VoiceController(
            microphone_probe=lambda: True,
            listen_for_command=lambda: "open chrome",
            process_command=lambda command: processed.append(command) or "Opening Chrome.",
            tts_queue=TTSQueue(playback=spoken.append),
        )

        result = controller.handle_wake_phrase("jarvis")

        self.assertEqual(result["status"], "processed")
        self.assertEqual(processed, ["open chrome"])
        self.assertEqual(spoken, ["Opening Chrome."])
        self.assertEqual(controller.state_machine.state, VoiceState.LISTENING_FOR_WAKE_WORD)

    def test_controller_disabled_voice_does_not_listen(self):
        controller = VoiceController(voice_enabled=False, microphone_probe=lambda: True, listen_for_command=lambda: "open chrome")

        result = controller.start()

        self.assertEqual(result["status"], "disabled")
        self.assertEqual(controller.state_machine.state, VoiceState.DISABLED)

    def test_controller_reports_missing_microphone_without_crashing(self):
        controller = VoiceController(microphone_probe=lambda: False, listen_for_command=lambda: "open chrome")

        result = controller.handle_wake_phrase("jarvis")

        self.assertEqual(result["status"], "microphone_unavailable")
        self.assertEqual(controller.state_machine.state, VoiceState.ERROR_RECOVERY)
