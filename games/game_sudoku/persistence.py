"""Progress, best times, and preferences for Sudoku."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from games.common.json_store import (
    choice_or_default,
    is_non_negative_int,
    load_json_object,
    save_json_object,
)
from games.common.types import Language

from .config import DEFAULT_LANGUAGE, DEFAULT_THEME, TEXTS, THEMES
from .puzzles import DIFFICULTY_ORDER, Difficulty, level_count, level_key

PLAYER_DATA_PATH = Path(__file__).with_name(".player_data.json")


@dataclass(frozen=True)
class PlayerData:
    best_times_ms: dict[str, int] = field(default_factory=dict)
    theme: str = DEFAULT_THEME
    language: Language = DEFAULT_LANGUAGE
    difficulty: Difficulty = "easy"
    level_index: int = 0


def _valid_level_key(key: object) -> bool:
    if not isinstance(key, str) or ":" not in key:
        return False
    difficulty, number = key.split(":", maxsplit=1)
    if difficulty not in DIFFICULTY_ORDER or not number.isdigit():
        return False
    return 1 <= int(number) <= level_count(difficulty)


def load_player_data(path: Path = PLAYER_DATA_PATH) -> PlayerData:
    payload = load_json_object(path)
    if payload is None:
        return PlayerData()
    raw_times = payload.get("best_times_ms")
    best_times: dict[str, int] = {}
    if isinstance(raw_times, dict):
        best_times = {
            key: value
            for key, value in raw_times.items()
            if _valid_level_key(key) and is_non_negative_int(value)
        }
    difficulty = choice_or_default(
        payload.get("difficulty"), DIFFICULTY_ORDER, "easy"
    )
    raw_index = payload.get("level_index")
    level_index = (
        raw_index
        if is_non_negative_int(raw_index) and raw_index < level_count(difficulty)
        else 0
    )
    return PlayerData(
        best_times_ms=best_times,
        theme=choice_or_default(payload.get("theme"), THEMES, DEFAULT_THEME),
        language=choice_or_default(payload.get("language"), TEXTS, DEFAULT_LANGUAGE),
        difficulty=difficulty,
        level_index=level_index,
    )


def save_player_data(data: PlayerData, path: Path = PLAYER_DATA_PATH) -> bool:
    if (
        data.theme not in THEMES
        or data.language not in TEXTS
        or data.difficulty not in DIFFICULTY_ORDER
        or not 0 <= data.level_index < level_count(data.difficulty)
    ):
        return False
    if any(
        not _valid_level_key(key) or not is_non_negative_int(value)
        for key, value in data.best_times_ms.items()
    ):
        return False
    return save_json_object(
        path,
        {
            "best_times_ms": data.best_times_ms,
            "theme": data.theme,
            "language": data.language,
            "difficulty": data.difficulty,
            "level_index": data.level_index,
        },
    )


def record_completion(
    data: PlayerData,
    difficulty: Difficulty,
    level_index: int,
    elapsed_ms: int,
) -> PlayerData:
    if elapsed_ms < 0:
        raise ValueError("Completion time must not be negative.")
    key = level_key(difficulty, level_index)
    previous = data.best_times_ms.get(key)
    if previous is not None and previous <= elapsed_ms:
        return data
    times = dict(data.best_times_ms)
    times[key] = elapsed_ms
    return replace(data, best_times_ms=times)
