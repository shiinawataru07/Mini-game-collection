"""Pure state transitions for the Sudoku game."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from .puzzles import Difficulty, SudokuLevel, get_level
from .solver import Grid, Position, candidates

GameStatus = Literal["playing", "paused", "won"]
GameEvent = Literal["placed", "note", "error", "cleared", "hint", "won", "undo", "redo"]
Notes = tuple[tuple[frozenset[int], ...], ...]


@dataclass(frozen=True)
class BoardSnapshot:
    values: Grid
    notes: Notes
    mistakes: int
    hints_used: int


@dataclass(frozen=True)
class GameState:
    level: SudokuLevel
    values: Grid
    notes: Notes
    selected: Position | None = None
    status: GameStatus = "playing"
    elapsed_ms: int = 0
    mistakes: int = 0
    hints_used: int = 0
    note_mode: bool = False
    history: tuple[BoardSnapshot, ...] = ()
    future: tuple[BoardSnapshot, ...] = ()

    @property
    def difficulty(self) -> Difficulty:
        return self.level.difficulty


@dataclass(frozen=True)
class Transition:
    state: GameState
    events: tuple[GameEvent, ...] = ()


def empty_notes() -> Notes:
    return tuple(tuple(frozenset() for _ in range(9)) for _ in range(9))


def new_game(difficulty: Difficulty = "easy", level_index: int = 0) -> GameState:
    level = get_level(difficulty, level_index)
    return GameState(level=level, values=level.puzzle, notes=empty_notes())


def is_given(state: GameState, position: Position) -> bool:
    row, column = position
    return state.level.puzzle[row][column] != 0


def _valid_position(position: Position) -> bool:
    return all(0 <= coordinate < 9 for coordinate in position)


def select_cell(state: GameState, position: Position | None) -> GameState:
    if position is not None and not _valid_position(position):
        raise ValueError("Sudoku position is outside the board.")
    return replace(state, selected=position)


def move_selection(state: GameState, dy: int, dx: int) -> GameState:
    if state.selected is None:
        return replace(state, selected=(0, 0))
    row, column = state.selected
    return replace(state, selected=((row + dy) % 9, (column + dx) % 9))


def toggle_note_mode(state: GameState) -> GameState:
    if state.status != "playing":
        return state
    return replace(state, note_mode=not state.note_mode)


def _snapshot(state: GameState) -> BoardSnapshot:
    return BoardSnapshot(state.values, state.notes, state.mistakes, state.hints_used)


def _replace_grid_value(grid: Grid, position: Position, value: int) -> Grid:
    row, column = position
    mutable = [list(values) for values in grid]
    mutable[row][column] = value
    return tuple(tuple(values) for values in mutable)


def _replace_note(notes: Notes, position: Position, values: frozenset[int]) -> Notes:
    row, column = position
    mutable = [list(cell_notes) for cell_notes in notes]
    mutable[row][column] = values
    return tuple(tuple(cell_notes) for cell_notes in mutable)


def _peers(position: Position) -> frozenset[Position]:
    row, column = position
    peers = {(row, index) for index in range(9)}
    peers.update((index, column) for index in range(9))
    box_row = row // 3 * 3
    box_column = column // 3 * 3
    peers.update(
        (box_row + dy, box_column + dx) for dy in range(3) for dx in range(3)
    )
    peers.discard(position)
    return frozenset(peers)


def _remove_peer_notes(notes: Notes, position: Position, value: int) -> Notes:
    updated = notes
    for peer in _peers(position):
        row, column = peer
        if value in updated[row][column]:
            updated = _replace_note(updated, peer, updated[row][column].difference((value,)))
    return updated


def _record_change(state: GameState, **changes) -> GameState:
    history = (state.history + (_snapshot(state),))[-100:]
    return replace(state, history=history, future=(), **changes)


def set_value(state: GameState, value: int) -> Transition:
    if value not in range(1, 10):
        raise ValueError("Sudoku values must be between 1 and 9.")
    position = state.selected
    if state.status != "playing" or position is None or is_given(state, position):
        return Transition(state)
    row, column = position
    if state.note_mode:
        if state.values[row][column]:
            return Transition(state)
        cell_notes = state.notes[row][column]
        updated_notes = (
            cell_notes.difference((value,)) if value in cell_notes else cell_notes.union((value,))
        )
        return Transition(
            _record_change(state, notes=_replace_note(state.notes, position, updated_notes)),
            ("note",),
        )
    if state.values[row][column] == value:
        return Transition(state)
    values = _replace_grid_value(state.values, position, value)
    notes = _replace_note(state.notes, position, frozenset())
    notes = _remove_peer_notes(notes, position, value)
    incorrect = value != state.level.solution[row][column]
    updated = _record_change(
        state,
        values=values,
        notes=notes,
        mistakes=state.mistakes + int(incorrect),
    )
    events: tuple[GameEvent, ...] = ("placed",)
    if incorrect:
        events += ("error",)
    elif values == state.level.solution:
        updated = replace(updated, status="won")
        events += ("won",)
    return Transition(updated, events)


def clear_selected(state: GameState) -> Transition:
    position = state.selected
    if state.status != "playing" or position is None or is_given(state, position):
        return Transition(state)
    row, column = position
    if not state.values[row][column] and not state.notes[row][column]:
        return Transition(state)
    return Transition(
        _record_change(
            state,
            values=_replace_grid_value(state.values, position, 0),
            notes=_replace_note(state.notes, position, frozenset()),
        ),
        ("cleared",),
    )


def apply_hint(state: GameState) -> Transition:
    if state.status != "playing":
        return Transition(state)
    target = state.selected
    if (
        target is None
        or is_given(state, target)
        or state.values[target[0]][target[1]] == state.level.solution[target[0]][target[1]]
    ):
        target = next(
            (
                (row, column)
                for row in range(9)
                for column in range(9)
                if not is_given(state, (row, column))
                and state.values[row][column] != state.level.solution[row][column]
            ),
            None,
        )
    if target is None:
        return Transition(state)
    value = state.level.solution[target[0]][target[1]]
    values = _replace_grid_value(state.values, target, value)
    notes = _replace_note(state.notes, target, frozenset())
    notes = _remove_peer_notes(notes, target, value)
    updated = _record_change(
        state,
        values=values,
        notes=notes,
        hints_used=state.hints_used + 1,
        selected=target,
    )
    events: tuple[GameEvent, ...] = ("hint",)
    if values == state.level.solution:
        updated = replace(updated, status="won")
        events += ("won",)
    return Transition(updated, events)


def _restore(state: GameState, snapshot: BoardSnapshot) -> GameState:
    status: GameStatus = "won" if snapshot.values == state.level.solution else "playing"
    return replace(
        state,
        values=snapshot.values,
        notes=snapshot.notes,
        mistakes=snapshot.mistakes,
        hints_used=snapshot.hints_used,
        status=status,
    )


def undo(state: GameState) -> Transition:
    if not state.history or state.status == "paused":
        return Transition(state)
    snapshot = state.history[-1]
    restored = _restore(state, snapshot)
    restored = replace(
        restored,
        history=state.history[:-1],
        future=(_snapshot(state),) + state.future,
    )
    return Transition(restored, ("undo",))


def redo(state: GameState) -> Transition:
    if not state.future or state.status == "paused":
        return Transition(state)
    snapshot = state.future[0]
    restored = _restore(state, snapshot)
    restored = replace(
        restored,
        history=state.history + (_snapshot(state),),
        future=state.future[1:],
    )
    return Transition(restored, ("redo",))


def advance_time(state: GameState, elapsed_ms: int) -> GameState:
    if elapsed_ms < 0:
        raise ValueError("Elapsed time must not be negative.")
    if state.status != "playing":
        return state
    return replace(state, elapsed_ms=state.elapsed_ms + elapsed_ms)


def toggle_pause(state: GameState) -> GameState:
    if state.status == "playing":
        return replace(state, status="paused")
    if state.status == "paused":
        return replace(state, status="playing")
    return state


def conflicting_positions(state: GameState) -> frozenset[Position]:
    conflicts: set[Position] = set()
    units: list[list[Position]] = []
    units.extend([[(row, column) for column in range(9)] for row in range(9)])
    units.extend([[(row, column) for row in range(9)] for column in range(9)])
    units.extend(
        [
            [(box_row + dy, box_column + dx) for dy in range(3) for dx in range(3)]
            for box_row in range(0, 9, 3)
            for box_column in range(0, 9, 3)
        ]
    )
    for unit in units:
        by_value: dict[int, list[Position]] = {}
        for position in unit:
            value = state.values[position[0]][position[1]]
            if value:
                by_value.setdefault(value, []).append(position)
        for positions in by_value.values():
            if len(positions) > 1:
                conflicts.update(positions)
    return frozenset(conflicts)


def wrong_positions(state: GameState) -> frozenset[Position]:
    return frozenset(
        (row, column)
        for row in range(9)
        for column in range(9)
        if not is_given(state, (row, column))
        and state.values[row][column]
        and state.values[row][column] != state.level.solution[row][column]
    )


def legal_candidates(state: GameState, position: Position) -> frozenset[int]:
    return candidates(state.values, position)
