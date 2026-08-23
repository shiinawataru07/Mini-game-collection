"""Repeatable command-line performance smoke benchmark for the Gomoku AI."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from ..logic import GameState, place_stone
from .api import Difficulty, choose_move, limits_for_difficulty


@dataclass(frozen=True)
class BenchmarkRow:
    difficulty: Difficulty
    median_ms: int
    median_nodes: int
    minimum_depth: int


def representative_position() -> GameState:
    state = GameState(
        tuple(tuple(0 for _ in range(15)) for _ in range(15)),
        mode="ai",
    )
    for move in ((7, 7), (7, 8), (8, 8), (6, 6), (8, 7)):
        result = place_stone(state, move)
        if not result.placed:
            raise RuntimeError(f"Invalid benchmark move: {move}")
        state = result.state
    return state


def run_benchmark(repeats: int = 3) -> tuple[BenchmarkRow, ...]:
    if repeats < 1:
        raise ValueError("Benchmark repeats must be at least one")
    state = representative_position()
    rows = []
    for difficulty in ("easy", "normal", "expert"):
        results = [choose_move(state, limits_for_difficulty(difficulty)) for _ in range(repeats)]
        rows.append(
            BenchmarkRow(
                difficulty,
                round(median(result.elapsed_ms for result in results)),
                round(median(result.nodes for result in results)),
                min(result.depth for result in results),
            )
        )
    return tuple(rows)


def main() -> None:
    print("difficulty  median_ms  median_nodes  minimum_depth")
    for row in run_benchmark():
        print(
            f"{row.difficulty:<10}  {row.median_ms:>9}  "
            f"{row.median_nodes:>12}  {row.minimum_depth:>13}"
        )


if __name__ == "__main__":
    main()
