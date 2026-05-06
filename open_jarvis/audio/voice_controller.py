"""Optional voice controller with injected hardware/runtime dependencies."""

from __future__ import annotations

from collections.abc import Callable

from open_jarvis.audio.microphone import microphone_available
from open_jarvis.audio.tts_queue import TTSQueue
from open_jarvis.audio.voice_state import VoiceState, VoiceStateMachine
from open_jarvis.audio.wake_word import WakeWordConfig, wake_word_detected


class VoiceController:
    def __init__(
        self,
        *,
        voice_enabled: bool = True,
        wake_word: str = "jarvis",
        microphone_probe: Callable[[], bool] | None = None,
        listen_for_command: Callable[[], str] | None = None,
        process_command: Callable[[str], object] | None = None,
        tts_queue: TTSQueue | None = None,
        state_machine: VoiceStateMachine | None = None,
    ) -> None:
        self.voice_enabled = voice_enabled
        self.wake_word = wake_word
        self.microphone_probe = microphone_probe
        self.listen_for_command = listen_for_command or (lambda: "")
        self.process_command = process_command or (lambda command: None)
        self.tts_queue = tts_queue
        self.state_machine = state_machine or VoiceStateMachine()

    def start(self) -> dict[str, object]:
        if not self.voice_enabled:
            self.state_machine.force(VoiceState.DISABLED, detail="voice disabled")
            return {"status": "disabled", "message": "[WARN] Voice mode disabled."}
        if not microphone_available(self.microphone_probe):
            self.state_machine.force(VoiceState.ERROR_RECOVERY, detail="microphone unavailable")
            return {"status": "microphone_unavailable", "message": "[WARN] Microphone unavailable. Voice input disabled."}
        self.state_machine.transition(VoiceState.LISTENING_FOR_WAKE_WORD, detail="voice ready")
        return {"status": "listening_for_wake_word"}

    def stop(self) -> dict[str, object]:
        self.state_machine.force(VoiceState.DISABLED, detail="voice stopped")
        return {"status": "stopped"}

    def handle_wake_phrase(self, phrase: str) -> dict[str, object]:
        if not self.voice_enabled:
            self.state_machine.force(VoiceState.DISABLED, detail="voice disabled")
            return {"status": "disabled"}
        if not wake_word_detected(phrase, config=WakeWordConfig(wake_word=self.wake_word, enabled=True)):
            return {"status": "ignored", "wake_word": self.wake_word}
        if not microphone_available(self.microphone_probe):
            self.state_machine.force(VoiceState.ERROR_RECOVERY, detail="microphone unavailable")
            return {"status": "microphone_unavailable"}
        self.state_machine.transition(VoiceState.LISTENING_FOR_WAKE_WORD)
        self.state_machine.transition(VoiceState.WAKE_WORD_DETECTED)
        return self._process_command_flow()

    def handle_push_to_talk(self) -> dict[str, object]:
        if not self.voice_enabled:
            self.state_machine.force(VoiceState.DISABLED, detail="voice disabled")
            return {"status": "disabled"}
        if not microphone_available(self.microphone_probe):
            self.state_machine.force(VoiceState.ERROR_RECOVERY, detail="microphone unavailable")
            return {"status": "microphone_unavailable"}
        self.state_machine.force(VoiceState.LISTENING_FOR_COMMAND, detail="push-to-talk")
        return self._process_command_flow()

    def _process_command_flow(self) -> dict[str, object]:
        try:
            if self.state_machine.state != VoiceState.LISTENING_FOR_COMMAND:
                self.state_machine.transition(VoiceState.LISTENING_FOR_COMMAND)
            command = self.listen_for_command()
            self.state_machine.transition(VoiceState.PROCESSING_COMMAND)
            result = self.process_command(command)
            tts_result: dict[str, object] | None = None
            if self.tts_queue is not None and result:
                self.state_machine.transition(VoiceState.SPEAKING_RESPONSE)
                self.tts_queue.enqueue(str(result))
                tts_result = self.tts_queue.drain_next()
            self.state_machine.force(VoiceState.LISTENING_FOR_WAKE_WORD, detail="command complete")
            return {"status": "processed", "command": command, "result": result, "tts": tts_result}
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            self.state_machine.force(VoiceState.ERROR_RECOVERY, detail=str(exc))
            return {"status": "voice_error", "error": str(exc)}
