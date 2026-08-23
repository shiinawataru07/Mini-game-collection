"""Stable public API for the Gomoku engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from ..logic import GameState, Position

Difficulty = Literal["easy", "normal", "expert"]


@dataclass(frozen=True)
class SearchLimits:
    time_ms: int = 700
    max_depth: int | None = 5
    max_nodes: int | None = None
    vcf_depth: int = 6
    table_capacity: int = 32_768

    def __post_init__(self) -> None:
        if self.time_ms < 1:
            raise ValueError("Search time must be at least 1 ms")
        if self.max_depth is not None and self.max_depth < 1:
            raise ValueError("Search depth must be at least 1")
        if self.max_nodes is not None and self.max_nodes < 1:
            raise ValueError("Search node limit must be at least 1")
        if self.vcf_depth < 0:
            raise ValueError("VCF depth cannot be negative")
        if self.table_capacity < 1:
            raise ValueError("Transposition table must contain at least one entry")


@dataclass(frozen=True)
class SearchResult:
    move: Position | None
    score: int
    depth: int
    nodes: int
    elapsed_ms: int
    principal_variation: tuple[Position, ...]
    forced_win: bool = False


DIFFICULTY_LIMITS: dict[Difficulty, SearchLimits] = {
    "easy": SearchLimits(time_ms=180, max_depth=2, vcf_depth=2, table_capacity=8_192),
    "normal": SearchLimits(time_ms=700, max_depth=5, vcf_depth=6, table_capacity=32_768),
    "expert": SearchLimits(time_ms=1_800, max_depth=8, vcf_depth=10, table_capacity=131_072),
}


def limits_for_difficulty(difficulty: Difficulty) -> SearchLimits:
    try:
        return DIFFICULTY_LIMITS[difficulty]
    except KeyError as error:
        raise ValueError(f"Unsupported AI difficulty: {difficulty}") from error


def choose_move(
    state: GameState,
    limits: SearchLimits | None = None,
    cancel: Callable[[], bool] | None = None,
) -> SearchResult:
    """Choose a legal move without mutating ``state``."""

    from .search import run_search

    return run_search(state, limits or SearchLimits(), cancel)
