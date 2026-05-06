"""Deterministic TTS queue for optional speech output."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

Playback = Callable[[str], None]


@dataclass
class TTSQueue:
    playback: Playback
    enabled: bool = True
    _queue: deque[str] = field(default_factory=deque)
    _speaking: bool = False
    _stopped: bool = False

    def enqueue(self, text: str) -> dict[str, object]:
        clean_text = str(text).strip()
        if not self.enabled:
            return {"status": "disabled", "queued": False, "pending": len(self._queue)}
        if not clean_text:
            return {"status": "empty", "queued": False, "pending": len(self._queue)}
        self._queue.append(clean_text)
        self._stopped = False
        return {"status": "queued", "queued": True, "pending": len(self._queue)}

    def drain_next(self) -> dict[str, object]:
        if not self.enabled:
            return {"status": "disabled", "spoken": False}
        if self._stopped:
            return {"status": "stopped", "spoken": False}
        if self._speaking:
            return {"status": "busy", "spoken": False}
        if not self._queue:
            return {"status": "empty", "spoken": False}
        text = self._queue.popleft()
        self._speaking = True
        try:
            self.playback(text)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return {"status": "failed", "spoken": False, "error": str(exc)}
        finally:
            self._speaking = False
        return {"status": "spoken", "spoken": True, "text": text, "pending": len(self._queue)}

    def drain_all(self) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        while self._queue and not self._stopped:
            result = self.drain_next()
            results.append(result)
            if result["status"] in {"busy", "failed", "disabled"}:
                break
        return results

    def stop(self) -> dict[str, object]:
        self._stopped = True
        self._speaking = False
        return {"status": "stopped", "pending": len(self._queue)}

    def clear(self) -> dict[str, object]:
        cleared = len(self._queue)
        self._queue.clear()
        return {"status": "cleared", "cleared": cleared}

    def is_speaking(self) -> bool:
        return self._speaking

    def pending_count(self) -> int:
        return len(self._queue)
