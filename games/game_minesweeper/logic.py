"""Pygame-independent Minesweeper rules and state transitions."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, replace
from typing import Literal

from .config import (
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    Difficulty,
    DifficultySpec,
    max_custom_mines,
)

CellVisibility = Literal["hidden", "revealed", "flagged", "questioned"]
GameStatus = Literal["ready", "running", "won", "lost"]
Position = tuple[int, int]
MAX_GENERATION_ATTEMPTS = 10_000


@dataclass(frozen=True)
class Cell:
    has_mine: bool = False
    adjacent_mines: int = 0
    visibility: CellVisibility = "hidden"


Board = tuple[tuple[Cell, ...], ...]


@dataclass(frozen=True)
class GameState:
    width: int
    height: int
    mine_count: int
    board: Board
    difficulty: Difficulty = DEFAULT_DIFFICULTY
    status: GameStatus = "ready"
    mines_placed: bool = False
    revealed_count: int = 0
    flag_count: int = 0
    elapsed_ms: int = 0
    exploded_cell: Position | None = None


@dataclass(frozen=True)
class ActionResult:
    state: GameState
    revealed_cells: tuple[Position, ...] = ()
    triggered_mine: Position | None = None


def new_game(difficulty: Difficulty = DEFAULT_DIFFICULTY) -> GameState:
    try:
        spec = DIFFICULTIES[difficulty]
    except KeyError as error:
        raise ValueError(f"Unsupported Minesweeper difficulty: {difficulty}") from error
    board = tuple(tuple(Cell() for _ in range(spec.width)) for _ in range(spec.height))
    return GameState(spec.width, spec.height, spec.mines, board, difficulty)


def new_custom_game(width: int, height: int, mine_count: int) -> GameState:
    """Create a custom board after strict range and density validation."""

    if not (8 <= width <= 30):
        raise ValueError("Custom width must be between 8 and 30.")
    if not (8 <= height <= 20):
        raise ValueError("Custom height must be between 8 and 20.")
    if not (1 <= mine_count <= max_custom_mines(width, height)):
        raise ValueError("Custom mine count exceeds the supported density.")
    spec = DifficultySpec(width, height, mine_count)
    board = tuple(tuple(Cell() for _ in range(spec.width)) for _ in range(spec.height))
    return GameState(spec.width, spec.height, spec.mines, board, "custom")


def _validate_position(state: GameState, position: Position) -> None:
    row, column = position
    if not (0 <= row < state.height and 0 <= column < state.width):
        raise ValueError(f"Cell is outside the board: {position}")


def neighbors(state: GameState, position: Position) -> tuple[Position, ...]:
    _validate_position(state, position)
    row, column = position
    return tuple(
        (neighbor_row, neighbor_column)
        for neighbor_row in range(max(0, row - 1), min(state.height, row + 2))
        for neighbor_column in range(max(0, column - 1), min(state.width, column + 2))
        if (neighbor_row, neighbor_column) != position
    )


def _with_cell(board: Board, position: Position, cell: Cell) -> Board:
    row, column = position
    rows = [list(board_row) for board_row in board]
    rows[row][column] = cell
    return tuple(tuple(board_row) for board_row in rows)


def _board_with_mines(state: GameState, mines: set[Position]) -> Board:
    board_rows: list[tuple[Cell, ...]] = []
    for row in range(state.height):
        cells: list[Cell] = []
        for column in range(state.width):
            position = (row, column)
            mine = position in mines
            adjacent = 0
            if not mine:
                adjacent = sum(neighbor in mines for neighbor in neighbors(state, position))
            original = state.board[row][column]
            cells.append(Cell(mine, adjacent, original.visibility))
        board_rows.append(tuple(cells))
    return tuple(board_rows)


def place_mines(
    state: GameState,
    first_reveal: Position,
    rng=None,
    require_solvable: bool = True,
) -> GameState:
    """Place a first-click-safe board that the deterministic solver can finish."""

    _validate_position(state, first_reveal)
    if state.mines_placed:
        return state
    safe_cells = {first_reveal, *neighbors(state, first_reveal)}
    candidates = [
        (row, column)
        for row in range(state.height)
        for column in range(state.width)
        if (row, column) not in safe_cells
    ]
    if len(candidates) < state.mine_count:
        raise ValueError("The board is too dense for a safe first reveal.")
    random_source = rng or random
    for _ in range(MAX_GENERATION_ATTEMPTS):
        mines = set(random_source.sample(candidates, state.mine_count))
        candidate = replace(
            state,
            board=_board_with_mines(state, mines),
            mines_placed=True,
            status="running",
        )
        if not require_solvable:
            return candidate
        from .solver import solve_from_first_reveal

        if solve_from_first_reveal(candidate, first_reveal):
            return candidate
    raise RuntimeError("Could not generate a logic-solvable Minesweeper board.")


def _expand_safe_cells(
    state: GameState, starts: tuple[Position, ...]
) -> tuple[Board, tuple[Position, ...]]:
    board = state.board
    pending: deque[Position] = deque(starts)
    queued = set(starts)
    revealed: list[Position] = []
    while pending:
        position = pending.popleft()
        cell = board[position[0]][position[1]]
        if cell.visibility not in ("hidden", "questioned") or cell.has_mine:
            continue
        board = _with_cell(board, position, replace(cell, visibility="revealed"))
        revealed.append(position)
        if cell.adjacent_mines == 0:
            for neighbor in neighbors(state, position):
                neighbor_cell = board[neighbor[0]][neighbor[1]]
                if neighbor_cell.visibility in ("hidden", "questioned") and neighbor not in queued:
                    queued.add(neighbor)
                    pending.append(neighbor)
    return board, tuple(revealed)


def _finish_reveal(
    state: GameState,
    board: Board,
    revealed: tuple[Position, ...],
) -> ActionResult:
    revealed_count = state.revealed_count + len(revealed)
    status: GameStatus = state.status
    flag_count = state.flag_count
    if revealed_count == state.width * state.height - state.mine_count:
        status = "won"
        rows = [list(row) for row in board]
        for row in range(state.height):
            for column in range(state.width):
                cell = rows[row][column]
                if cell.has_mine and cell.visibility in ("hidden", "questioned"):
                    rows[row][column] = replace(cell, visibility="flagged")
        board = tuple(tuple(row) for row in rows)
        flag_count = state.mine_count
    return ActionResult(
        replace(
            state,
            board=board,
            revealed_count=revealed_count,
            flag_count=flag_count,
            status=status,
        ),
        revealed,
    )


def reveal_cell(state: GameState, position: Position, rng=None) -> ActionResult:
    """Reveal a cell, placing mines lazily and expanding empty regions."""

    _validate_position(state, position)
    if state.status in ("won", "lost"):
        return ActionResult(state)
    cell = state.board[position[0]][position[1]]
    if cell.visibility == "flagged":
        return ActionResult(state)
    if cell.visibility == "revealed":
        return chord_cell(state, position)
    if not state.mines_placed:
        state = place_mines(state, position, rng)
        cell = state.board[position[0]][position[1]]
    if cell.has_mine:
        lost = replace(state, status="lost", exploded_cell=position)
        return ActionResult(lost, triggered_mine=position)
    board, revealed = _expand_safe_cells(state, (position,))
    return _finish_reveal(state, board, revealed)


def cycle_mark(state: GameState, position: Position) -> GameState:
    """Cycle an unrevealed cell through flag, question mark, and no mark."""

    _validate_position(state, position)
    if state.status in ("won", "lost"):
        return state
    cell = state.board[position[0]][position[1]]
    if cell.visibility == "revealed":
        return state
    if cell.visibility == "hidden":
        visibility: CellVisibility = "flagged"
        flag_delta = 1
    elif cell.visibility == "flagged":
        visibility = "questioned"
        flag_delta = -1
    else:
        visibility = "hidden"
        flag_delta = 0
    board = _with_cell(state.board, position, replace(cell, visibility=visibility))
    return replace(state, board=board, flag_count=state.flag_count + flag_delta)


def toggle_flag(state: GameState, position: Position) -> GameState:
    """Backward-compatible alias for the three-state mark cycle."""

    return cycle_mark(state, position)


def chord_cell(state: GameState, position: Position) -> ActionResult:
    """Reveal neighbors when a number has exactly that many adjacent flags."""

    _validate_position(state, position)
    if state.status != "running":
        return ActionResult(state)
    cell = state.board[position[0]][position[1]]
    if cell.visibility != "revealed" or cell.adjacent_mines == 0:
        return ActionResult(state)
    adjacent = neighbors(state, position)
    flagged = sum(state.board[row][column].visibility == "flagged" for row, column in adjacent)
    if flagged != cell.adjacent_mines:
        return ActionResult(state)
    hidden = tuple(
        neighbor
        for neighbor in adjacent
        if state.board[neighbor[0]][neighbor[1]].visibility in ("hidden", "questioned")
    )
    triggered = next(
        (neighbor for neighbor in hidden if state.board[neighbor[0]][neighbor[1]].has_mine),
        None,
    )
    if triggered is not None:
        lost = replace(state, status="lost", exploded_cell=triggered)
        return ActionResult(lost, triggered_mine=triggered)
    board, revealed = _expand_safe_cells(state, hidden)
    return _finish_reveal(state, board, revealed)


def advance_time(state: GameState, elapsed_ms: int) -> GameState:
    if elapsed_ms < 0:
        raise ValueError("Elapsed time must not be negative.")
    if state.status != "running" or elapsed_ms == 0:
        return state
    return replace(state, elapsed_ms=state.elapsed_ms + elapsed_ms)


def remaining_mines(state: GameState) -> int:
    return state.mine_count - state.flag_count
