"""Bundled Sudoku campaign metadata and level loading."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .levels import LEVEL_DATA
from .solver import Grid, parse_grid

Difficulty = Literal["easy", "medium", "hard"]
DIFFICULTY_ORDER: tuple[Difficulty, ...] = ("easy", "medium", "hard")
CLUE_COUNTS: dict[Difficulty, int] = {"easy": 40, "medium": 35, "hard": 30}


@dataclass(frozen=True)
class SudokuLevel:
    difficulty: Difficulty
    index: int
    puzzle: Grid
    solution: Grid

    @property
    def number(self) -> int:
        return self.index + 1

    @property
    def clue_count(self) -> int:
        return sum(value != 0 for row in self.puzzle for value in row)


def _load_levels() -> dict[Difficulty, tuple[SudokuLevel, ...]]:
    loaded: dict[Difficulty, tuple[SudokuLevel, ...]] = {}
    for difficulty in DIFFICULTY_ORDER:
        loaded[difficulty] = tuple(
            SudokuLevel(difficulty, index, parse_grid(puzzle), parse_grid(solution))
            for index, (puzzle, solution) in enumerate(LEVEL_DATA[difficulty])
        )
    return loaded


LEVELS = _load_levels()


def get_level(difficulty: Difficulty, index: int) -> SudokuLevel:
    if difficulty not in LEVELS:
        raise ValueError(f"Unknown Sudoku difficulty: {difficulty}")
    if not 0 <= index < len(LEVELS[difficulty]):
        raise ValueError(f"Sudoku level index is out of range: {index}")
    return LEVELS[difficulty][index]


def level_count(difficulty: Difficulty) -> int:
    if difficulty not in LEVELS:
        raise ValueError(f"Unknown Sudoku difficulty: {difficulty}")
    return len(LEVELS[difficulty])


def level_key(difficulty: Difficulty, index: int) -> str:
    get_level(difficulty, index)
    return f"{difficulty}:{index + 1}"
