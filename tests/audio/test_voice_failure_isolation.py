from unittest import TestCase

from open_jarvis.audio.tts_queue import TTSQueue
from open_jarvis.audio.voice_controller import VoiceController
from open_jarvis.audio.voice_state import VoiceState


class VoiceFailureIsolationTest(TestCase):
    def test_listener_failure_enters_error_recovery(self):
        controller = VoiceController(
            microphone_probe=lambda: True,
            listen_for_command=lambda: (_ for _ in ()).throw(RuntimeError("stt failed")),
        )

        result = controller.handle_wake_phrase("jarvis")

        self.assertEqual(result["status"], "voice_error")
        self.assertEqual(controller.state_machine.state, VoiceState.ERROR_RECOVERY)

    def test_tts_failure_does_not_fail_command_processing(self):
        processed = []
        controller = VoiceController(
            microphone_probe=lambda: True,
            listen_for_command=lambda: "open chrome",
            process_command=lambda command: processed.append(command) or "Opening Chrome.",
            tts_queue=TTSQueue(playback=lambda text: (_ for _ in ()).throw(RuntimeError("speaker missing"))),
        )

        result = controller.handle_wake_phrase("jarvis")

        self.assertEqual(result["status"], "processed")
        self.assertEqual(result["tts"]["status"], "failed")
        self.assertEqual(processed, ["open chrome"])
