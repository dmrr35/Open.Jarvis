from unittest import TestCase

from open_jarvis.audio.voice_state import VoiceState, VoiceStateMachine, transition_voice_state


class VoiceStateMachineTest(TestCase):
    def test_valid_transition_updates_state(self):
        machine = VoiceStateMachine()

        result = machine.transition(VoiceState.LISTENING_FOR_WAKE_WORD, detail="ready")

        self.assertTrue(result["ok"])
        self.assertEqual(machine.state, VoiceState.LISTENING_FOR_WAKE_WORD)
        self.assertEqual(result["detail"], "ready")

    def test_invalid_transition_returns_structured_result(self):
        result = transition_voice_state(VoiceState.IDLE, VoiceState.SPEAKING_RESPONSE)

        self.assertFalse(result["ok"])
        self.assertEqual(result["from"], "IDLE")
        self.assertEqual(result["to"], "SPEAKING_RESPONSE")
        self.assertIn("invalid", result["reason"])

    def test_disabled_mode_can_return_to_idle(self):
        machine = VoiceStateMachine(VoiceState.DISABLED)

        result = machine.transition(VoiceState.IDLE)

        self.assertTrue(result["ok"])
        self.assertEqual(machine.state, VoiceState.IDLE)
