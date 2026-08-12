"""Deterministic constraint solver and hint selection for Minesweeper."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from .logic import (
    Board,
    GameState,
    Position,
    cycle_mark,
    neighbors,
    reveal_cell,
)

HintKind = Literal["safe", "mine", "incorrect_flag"]
MAX_DERIVED_CONSTRAINTS = 2048


@dataclass(frozen=True)
class Deductions:
    """Cells proven safe or mined from currently visible information."""

    safe: frozenset[Position] = frozenset()
    mines: frozenset[Position] = frozenset()
    contradiction: bool = False


@dataclass(frozen=True)
class Hint:
    position: Position
    kind: HintKind


def _unknown_positions(state: GameState) -> frozenset[Position]:
    return frozenset(
        (row, column)
        for row in range(state.height)
        for column in range(state.width)
        if state.board[row][column].visibility in ("hidden", "questioned")
    )


def deduce(state: GameState) -> Deductions:
    """Apply direct, global, and subset rules without inspecting hidden mines."""

    if state.status not in ("ready", "running"):
        return Deductions()

    constraints: dict[frozenset[Position], int] = {}
    contradiction = False

    def add_constraint(cells: frozenset[Position], mine_count: int) -> bool:
        nonlocal contradiction
        if mine_count < 0 or mine_count > len(cells):
            contradiction = True
            return False
        if not cells:
            if mine_count:
                contradiction = True
            return False
        previous = constraints.get(cells)
        if previous is not None and previous != mine_count:
            contradiction = True
            return False
        if previous is None:
            constraints[cells] = mine_count
            return True
        return False

    for row in range(state.height):
        for column in range(state.width):
            cell = state.board[row][column]
            if cell.visibility != "revealed" or cell.adjacent_mines == 0:
                continue
            adjacent = neighbors(state, (row, column))
            flagged = sum(
                state.board[neighbor_row][neighbor_column].visibility == "flagged"
                for neighbor_row, neighbor_column in adjacent
            )
            unknown = frozenset(
                position
                for position in adjacent
                if state.board[position[0]][position[1]].visibility in ("hidden", "questioned")
            )
            add_constraint(unknown, cell.adjacent_mines - flagged)

    changed = True
    while changed and not contradiction and len(constraints) < MAX_DERIVED_CONSTRAINTS:
        changed = False
        items = list(constraints.items())
        for first_cells, first_mines in items:
            for second_cells, second_mines in items:
                if first_cells == second_cells or not first_cells.issubset(second_cells):
                    continue
                difference = second_cells - first_cells
                if add_constraint(difference, second_mines - first_mines):
                    changed = True
                    if len(constraints) >= MAX_DERIVED_CONSTRAINTS:
                        break
            if contradiction or len(constraints) >= MAX_DERIVED_CONSTRAINTS:
                break

    safe: set[Position] = set()
    mines: set[Position] = set()
    for cells, mine_count in constraints.items():
        if mine_count == 0:
            safe.update(cells)
        elif mine_count == len(cells):
            mines.update(cells)

    unknown = _unknown_positions(state)
    remaining = state.mine_count - state.flag_count
    if remaining < 0 or remaining > len(unknown):
        contradiction = True
    elif remaining == 0:
        safe.update(unknown)
    elif remaining == len(unknown):
        mines.update(unknown)

    if safe & mines:
        contradiction = True
    return Deductions(frozenset(safe), frozenset(mines), contradiction)


def _hidden_board(board: Board) -> Board:
    return tuple(tuple(replace(cell, visibility="hidden") for cell in row) for row in board)


def solve_from_first_reveal(state: GameState, first_reveal: Position) -> bool:
    """Return whether the placed board can be completed without guessing."""

    if not state.mines_placed:
        raise ValueError("The solver requires a board with placed mines.")
    simulation = replace(
        state,
        board=_hidden_board(state.board),
        status="running",
        revealed_count=0,
        flag_count=0,
        elapsed_ms=0,
        exploded_cell=None,
    )
    simulation = reveal_cell(simulation, first_reveal).state
    if simulation.status == "won":
        return True

    for _ in range(state.width * state.height * 2):
        deductions = deduce(simulation)
        if deductions.contradiction or (not deductions.safe and not deductions.mines):
            return False
        previous = simulation
        for position in sorted(deductions.mines):
            if simulation.board[position[0]][position[1]].visibility in (
                "hidden",
                "questioned",
            ):
                simulation = cycle_mark(simulation, position)
        for position in sorted(deductions.safe):
            if simulation.board[position[0]][position[1]].visibility in (
                "hidden",
                "questioned",
            ):
                simulation = reveal_cell(simulation, position).state
                if simulation.status == "lost":
                    return False
        if simulation.status == "won":
            return True
        if simulation == previous:
            return False
    return False


def find_hint(state: GameState) -> Hint | None:
    """Return one sound next move, guarding against incorrect player flags."""

    if state.status == "ready":
        return Hint((state.height // 2, state.width // 2), "safe")
    if state.status != "running":
        return None

    deductions = deduce(state)
    incorrect_flags = sorted(
        (row, column)
        for row in range(state.height)
        for column in range(state.width)
        if state.board[row][column].visibility == "flagged"
        and not state.board[row][column].has_mine
    )
    if deductions.contradiction and incorrect_flags:
        return Hint(incorrect_flags[0], "incorrect_flag")

    for position in sorted(deductions.safe):
        if not state.board[position[0]][position[1]].has_mine:
            return Hint(position, "safe")
    for position in sorted(deductions.mines):
        if state.board[position[0]][position[1]].has_mine:
            return Hint(position, "mine")
    if incorrect_flags:
        return Hint(incorrect_flags[0], "incorrect_flag")
    return None
