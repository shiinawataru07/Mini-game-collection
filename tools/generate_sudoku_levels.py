"""Regenerate the bundled Sudoku campaign with deterministic unique puzzles.

The 40 / 35 / 30 clue presets follow the public defaults documented by the
MIT-licensed generator at https://github.com/alicommit-malp/sudoku. The code
and generated puzzles in this project are independently implemented.
"""

from __future__ import annotations

import random
from pathlib import Path

from games.game_sudoku.solver import Grid, count_solutions, grid_string

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "games" / "game_sudoku" / "levels.py"
PRESETS = (("easy", 40), ("medium", 35), ("hard", 30))
LEVELS_PER_DIFFICULTY = 20


def _shuffled_groups(source: random.Random) -> list[int]:
    groups = list(range(3))
    source.shuffle(groups)
    result: list[int] = []
    for group in groups:
        members = list(range(3))
        source.shuffle(members)
        result.extend(group * 3 + member for member in members)
    return result


def solved_grid(seed: int) -> Grid:
    source = random.Random(seed)
    rows = _shuffled_groups(source)
    columns = _shuffled_groups(source)
    digits = list(range(1, 10))
    source.shuffle(digits)

    def pattern(row: int, column: int) -> int:
        return (row * 3 + row // 3 + column) % 9

    return tuple(
        tuple(digits[pattern(row, column)] for column in columns) for row in rows
    )


def generate_puzzle(seed: int, target_clues: int) -> tuple[Grid, Grid]:
    solution = solved_grid(seed)
    mutable = [list(row) for row in solution]
    positions = list(range(81))
    random.Random(seed ^ 0x5EED).shuffle(positions)
    clues = 81
    for position in positions:
        if clues <= target_clues:
            break
        row, column = divmod(position, 9)
        previous = mutable[row][column]
        mutable[row][column] = 0
        puzzle = tuple(tuple(values) for values in mutable)
        if count_solutions(puzzle) == 1:
            clues -= 1
        else:
            mutable[row][column] = previous
    if clues != target_clues:
        raise RuntimeError(f"Seed {seed} stopped at {clues} clues, target was {target_clues}.")
    return tuple(tuple(values) for values in mutable), solution


def generate_campaign() -> dict[str, list[tuple[str, str]]]:
    campaign: dict[str, list[tuple[str, str]]] = {}
    for difficulty_index, (difficulty, target_clues) in enumerate(PRESETS):
        levels: list[tuple[str, str]] = []
        attempt = 0
        while len(levels) < LEVELS_PER_DIFFICULTY:
            seed = 13_579 + difficulty_index * 100_000 + attempt
            attempt += 1
            try:
                puzzle, solution = generate_puzzle(seed, target_clues)
            except RuntimeError:
                continue
            encoded = (grid_string(puzzle), grid_string(solution))
            if encoded not in levels:
                levels.append(encoded)
        campaign[difficulty] = levels
    return campaign


def render_module(campaign: dict[str, list[tuple[str, str]]]) -> str:
    lines = [
        '"""Generated fixed Sudoku campaign. Regenerate with tools/generate_sudoku_levels.py."""',
        "",
        "from __future__ import annotations",
        "",
        "LEVEL_DATA: dict[str, tuple[tuple[str, str], ...]] = {",
    ]
    for difficulty, levels in campaign.items():
        lines.append(f'    "{difficulty}": (')
        for puzzle, solution in levels:
            lines.append(f'        ("{puzzle}", "{solution}"),')
        lines.append("    ),")
    lines.extend(("}", ""))
    return "\n".join(lines)


if __name__ == "__main__":
    OUTPUT.write_text(render_module(generate_campaign()), encoding="utf-8")
    print(f"Wrote {LEVELS_PER_DIFFICULTY * len(PRESETS)} levels to {OUTPUT}")
