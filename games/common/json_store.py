"""Defensive JSON-file storage and basic persisted-value validation."""

from __future__ import annotations

import json
from collections.abc import Container, Mapping
from pathlib import Path
from typing import Any, TypeVar, cast

JsonObject = dict[str, Any]
Choice = TypeVar("Choice")


def load_json_object(path: Path) -> JsonObject | None:
    """Read a JSON object, returning ``None`` for missing, corrupt, or non-object data."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def save_json_object(
    path: Path,
    payload: Mapping[str, Any],
    *,
    ensure_ascii: bool = False,
) -> bool:
    """Write a JSON object without allowing storage errors to interrupt a game."""

    try:
        path.write_text(
            json.dumps(dict(payload), ensure_ascii=ensure_ascii, indent=2),
            encoding="utf-8",
        )
        return True
    except (OSError, TypeError, ValueError):
        return False


def is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def non_negative_int(value: object, default: int = 0) -> int:
    return value if is_non_negative_int(value) else default


def choice_or_default(
    value: object,
    allowed: Container[Choice],
    default: Choice,
) -> Choice:
    """Return a persisted choice only when it belongs to the supported collection."""

    try:
        return cast(Choice, value) if value in allowed else default
    except TypeError:
        return default
