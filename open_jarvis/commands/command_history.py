"""Command history with optional undo callbacks."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from typing import Any


class CommandHistory:
    """Keep recent commands and provide a safe undo surface."""

    def __init__(self, limit: int = 50):
        self.limit = limit
        self._items: deque[dict[str, Any]] = deque(maxlen=limit)
        self._undo: dict[str, Callable[[], None]] = {}
        self._ids: set[str] = set()
        self._next_id = 0

    def record(self, command: str, undo: Callable[[], None] | None = None) -> dict[str, Any]:
        self._next_id += 1
        item = {
            "id": f"cmd-{self._next_id}",
            "command": command,
            "undoable": undo is not None,
            "created_at": time.time(),
        }
        if len(self._items) == self.limit and self._items:
            expired = self._items[0]
            expired_id = str(expired["id"])
            self._undo.pop(expired_id, None)
            self._ids.discard(expired_id)
        self._items.append(item)
        self._ids.add(str(item["id"]))
        if undo is not None:
            self._undo[str(item["id"])] = undo
        return item

    def list(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._items]

    def undo(self, command_id: str) -> dict[str, str]:
        if command_id not in self._ids:
            return {"status": "expired"}
        callback = self._undo.pop(command_id, None)
        if callback is None:
            return {"status": "not_undoable"}
        callback()
        return {"status": "undone"}
