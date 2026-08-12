"""Best-time and player-preference persistence for Minesweeper."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .config import (
    DEFAULT_DIFFICULTY,
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    DIFFICULTIES,
    TEXTS,
    THEMES,
    Difficulty,
    Language,
)

PLAYER_DATA_PATH = Path(__file__).with_name(".player_data.json")


def _default_best_times() -> dict[Difficulty, int | None]:
    return {difficulty: None for difficulty in DIFFICULTIES}


@dataclass(frozen=True)
class PlayerData:
    best_times_ms: dict[Difficulty, int | None] = field(default_factory=_default_best_times)
    theme: str = DEFAULT_THEME
    language: Language = DEFAULT_LANGUAGE
    difficulty: Difficulty = DEFAULT_DIFFICULTY


def load_player_data(path: Path = PLAYER_DATA_PATH) -> PlayerData:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_times = payload.get("best_times_ms", {})
        times = _default_best_times()
        if isinstance(raw_times, dict):
            for difficulty in DIFFICULTIES:
                value = raw_times.get(difficulty)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    times[difficulty] = value
        theme = payload.get("theme", DEFAULT_THEME)
        language = payload.get("language", DEFAULT_LANGUAGE)
        difficulty = payload.get("difficulty", DEFAULT_DIFFICULTY)
        if theme not in THEMES:
            theme = DEFAULT_THEME
        if language not in TEXTS:
            language = DEFAULT_LANGUAGE
        if difficulty not in DIFFICULTIES:
            difficulty = DEFAULT_DIFFICULTY
        return PlayerData(times, theme, language, difficulty)
    except (OSError, json.JSONDecodeError, AttributeError, TypeError):
        return PlayerData()


def update_best_time(data: PlayerData, difficulty: Difficulty, elapsed_ms: int) -> PlayerData:
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Unsupported Minesweeper difficulty: {difficulty}")
    if elapsed_ms < 0:
        raise ValueError("Best time must not be negative.")
    current = data.best_times_ms[difficulty]
    if current is not None and current <= elapsed_ms:
        return data
    times = dict(data.best_times_ms)
    times[difficulty] = elapsed_ms
    return PlayerData(times, data.theme, data.language, data.difficulty)


def save_player_data(data: PlayerData, path: Path = PLAYER_DATA_PATH) -> bool:
    if (
        data.theme not in THEMES
        or data.language not in TEXTS
        or data.difficulty not in DIFFICULTIES
    ):
        return False
    times: dict[str, int | None] = {}
    for difficulty in DIFFICULTIES:
        value = data.best_times_ms.get(difficulty)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            return False
        times[difficulty] = value
    payload = {
        "best_times_ms": times,
        "theme": data.theme,
        "language": data.language,
        "difficulty": data.difficulty,
    }
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False
