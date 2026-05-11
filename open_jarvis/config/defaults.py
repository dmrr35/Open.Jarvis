"""Built-in safe configuration defaults."""

from __future__ import annotations

import copy
from typing import Any

from open_jarvis.config.schema import FIELD_DEFINITIONS


def build_default_config() -> dict[str, dict[str, Any]]:
    config: dict[str, dict[str, Any]] = {}
    for field in FIELD_DEFINITIONS.values():
        config.setdefault(field.category, {})[field.name] = copy.deepcopy(field.default)
    return config
