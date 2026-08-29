"""Pure Sudoku parsing, solving, and uniqueness checks."""

from __future__ import annotations

from collections.abc import Sequence

GRID_SIZE = 9
BOX_SIZE = 3
DIGITS = frozenset(range(1, 10))
Grid = tuple[tuple[int, ...], ...]
Position = tuple[int, int]


def parse_grid(value: str) -> Grid:
    """Parse an 81-character puzzle where ``0`` and ``.`` are empty cells."""

    compact = "".join(character for character in value if not character.isspace())
    if len(compact) != GRID_SIZE * GRID_SIZE:
        raise ValueError("A Sudoku grid must contain exactly 81 cells.")
    if any(character not in "0123456789." for character in compact):
        raise ValueError("A Sudoku grid may only contain digits, zero, or dots.")
    values = [0 if character in "0." else int(character) for character in compact]
    grid = tuple(
        tuple(values[row * GRID_SIZE : (row + 1) * GRID_SIZE])
        for row in range(GRID_SIZE)
    )
    if not is_consistent(grid):
        raise ValueError("Sudoku givens contain a duplicate in a row, column, or box.")
    return grid


def grid_string(grid: Grid) -> str:
    return "".join(str(value) for row in grid for value in row)


def _units(grid: Grid) -> tuple[tuple[int, ...], ...]:
    rows = tuple(tuple(row) for row in grid)
    columns = tuple(tuple(grid[row][column] for row in range(9)) for column in range(9))
    boxes = tuple(
        tuple(
            grid[box_row + row][box_column + column]
            for row in range(3)
            for column in range(3)
        )
        for box_row in range(0, 9, 3)
        for box_column in range(0, 9, 3)
    )
    return rows + columns + boxes


def is_consistent(grid: Grid) -> bool:
    if len(grid) != 9 or any(len(row) != 9 for row in grid):
        return False
    if any(value not in range(10) for row in grid for value in row):
        return False
    for unit in _units(grid):
        filled = [value for value in unit if value]
        if len(filled) != len(set(filled)):
            return False
    return True


def candidates(grid: Grid, position: Position) -> frozenset[int]:
    row, column = position
    if not (0 <= row < 9 and 0 <= column < 9):
        raise ValueError("Sudoku position is outside the board.")
    if grid[row][column]:
        return frozenset()
    used = set(grid[row])
    used.update(grid[index][column] for index in range(9))
    box_row = row // 3 * 3
    box_column = column // 3 * 3
    used.update(
        grid[box_row + dy][box_column + dx]
        for dy in range(3)
        for dx in range(3)
    )
    return DIGITS.difference(used)


def _best_empty(grid: Grid) -> tuple[Position, frozenset[int]] | None:
    best: tuple[Position, frozenset[int]] | None = None
    for row in range(9):
        for column in range(9):
            if grid[row][column]:
                continue
            options = candidates(grid, (row, column))
            if not options:
                return (row, column), options
            if best is None or len(options) < len(best[1]):
                best = (row, column), options
                if len(options) == 1:
                    return best
    return best


def _replace_value(grid: Grid, position: Position, value: int) -> Grid:
    row, column = position
    mutable = [list(values) for values in grid]
    mutable[row][column] = value
    return tuple(tuple(values) for values in mutable)


def solve(grid: Grid) -> Grid | None:
    """Return one solution using MRV backtracking, or ``None`` if unsatisfiable."""

    if not is_consistent(grid):
        return None
    target = _best_empty(grid)
    if target is None:
        return grid
    position, options = target
    for value in sorted(options):
        solved = solve(_replace_value(grid, position, value))
        if solved is not None:
            return solved
    return None


def count_solutions(grid: Grid, limit: int = 2) -> int:
    """Count solutions up to ``limit`` so uniqueness checks can stop early."""

    if limit < 1:
        raise ValueError("Solution count limit must be positive.")
    if not is_consistent(grid):
        return 0

    count = 0

    def search(current: Grid) -> None:
        nonlocal count
        if count >= limit:
            return
        target = _best_empty(current)
        if target is None:
            count += 1
            return
        position, options = target
        for value in sorted(options):
            search(_replace_value(current, position, value))
            if count >= limit:
                return

    search(grid)
    return count


def grid_from_rows(rows: Sequence[Sequence[int]]) -> Grid:
    grid = tuple(tuple(row) for row in rows)
    if not is_consistent(grid):
        raise ValueError("Rows do not describe a consistent 9×9 Sudoku grid.")
    return grid
