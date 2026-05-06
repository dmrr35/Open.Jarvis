"""Push-to-talk fallback that bypasses wake-word detection safely."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from open_jarvis.audio.microphone import microphone_available

CommandListener = Callable[[], str]
CommandProcessor = Callable[[str], object]


@dataclass
class PushToTalkController:
    microphone_probe: Callable[[], bool] | None
    listen_for_command: CommandListener
    process_command: CommandProcessor
    active: bool = False

    def start(self) -> dict[str, object]:
        if not microphone_available(self.microphone_probe):
            self.active = False
            return {"status": "microphone_unavailable", "message": "[WARN] Microphone unavailable. Push-to-talk disabled."}
        self.active = True
        try:
            command = self.listen_for_command()
            if not command:
                return {"status": "empty", "command": ""}
            result = self.process_command(command)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return {"status": "voice_error", "error": str(exc)}
        finally:
            self.active = False
        return {"status": "processed", "command": command, "result": result}

    def stop(self) -> dict[str, object]:
        self.active = False
        return {"status": "stopped"}
