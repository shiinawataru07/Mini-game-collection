"""Pure Tetris rules with no dependency on Pygame or persistence."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import Literal

from .config import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    LOCK_DELAY_MS,
    MAX_LOCK_RESETS,
    NEXT_COUNT,
    gravity_interval_ms,
)
from .pieces import (
    PIECE_IDS,
    Cell,
    PieceKind,
    RotationDirection,
    cells,
    kick_offsets,
    rotated,
    shuffled_bag,
)

Board = tuple[tuple[int, ...], ...]
GameStatus = Literal["running", "paused", "game_over"]
GameEvent = Literal["moved", "rotated", "held", "locked", "lines_cleared", "game_over"]


@dataclass(frozen=True)
class ActivePiece:
    kind: PieceKind
    rotation: int = 0
    x: int = 3
    y: int = 0


@dataclass(frozen=True)
class GameState:
    board: Board
    active: ActivePiece
    next_queue: tuple[PieceKind, ...]
    bag: tuple[PieceKind, ...]
    hold: PieceKind | None = None
    hold_used: bool = False
    score: int = 0
    lines: int = 0
    level: int = 1
    combo: int = -1
    gravity_elapsed_ms: float = 0.0
    lock_elapsed_ms: float = 0.0
    lock_resets: int = 0
    status: GameStatus = "running"


@dataclass(frozen=True)
class Transition:
    state: GameState
    events: tuple[GameEvent, ...] = ()
    cleared_rows: tuple[int, ...] = ()
    drop_distance: int = 0
    gained_score: int = 0


def empty_board() -> Board:
    return tuple(tuple(0 for _ in range(BOARD_WIDTH)) for _ in range(BOARD_HEIGHT))


def _refill_queue(
    queue: tuple[PieceKind, ...],
    bag: tuple[PieceKind, ...],
    count: int,
    rng=None,
) -> tuple[tuple[PieceKind, ...], tuple[PieceKind, ...]]:
    source = rng or random
    pending = list(queue)
    remaining = list(bag)
    while len(pending) < count:
        if not remaining:
            remaining.extend(shuffled_bag(source))
        pending.append(remaining.pop(0))
    return tuple(pending), tuple(remaining)


def new_game(rng=None) -> GameState:
    queue, bag = _refill_queue((), (), NEXT_COUNT + 1, rng)
    active = ActivePiece(queue[0])
    return GameState(empty_board(), active, queue[1:], bag)


def active_cells(state: GameState) -> tuple[Cell, ...]:
    piece = state.active
    return cells(piece.kind, piece.rotation, piece.x, piece.y)


def can_place(board: Board, piece: ActivePiece) -> bool:
    for column, row in cells(piece.kind, piece.rotation, piece.x, piece.y):
        if column < 0 or column >= BOARD_WIDTH or row < 0 or row >= BOARD_HEIGHT:
            return False
        if board[row][column]:
            return False
    return True


def is_grounded(state: GameState) -> bool:
    return not can_place(state.board, replace(state.active, y=state.active.y + 1))


def ghost_y(state: GameState) -> int:
    piece = state.active
    y = piece.y
    while can_place(state.board, replace(piece, y=y + 1)):
        y += 1
    return y


def _after_player_transform(
    state: GameState,
    piece: ActivePiece,
    event: GameEvent,
) -> Transition:
    was_grounded = is_grounded(state)
    resets = state.lock_resets
    lock_elapsed = state.lock_elapsed_ms
    if was_grounded and resets < MAX_LOCK_RESETS:
        lock_elapsed = 0.0
        resets += 1
    return Transition(
        replace(
            state,
            active=piece,
            lock_elapsed_ms=lock_elapsed,
            lock_resets=resets,
        ),
        (event,),
    )


def move(state: GameState, dx: int) -> Transition:
    if state.status != "running" or dx not in (-1, 1):
        return Transition(state)
    moved = replace(state.active, x=state.active.x + dx)
    if not can_place(state.board, moved):
        return Transition(state)
    return _after_player_transform(state, moved, "moved")


def rotate(state: GameState, direction: RotationDirection) -> Transition:
    if state.status != "running":
        return Transition(state)
    piece = state.active
    target_rotation = rotated(piece.rotation, direction)
    for offset_x, offset_y in kick_offsets(piece.kind, piece.rotation, target_rotation):
        candidate = replace(
            piece,
            rotation=target_rotation,
            x=piece.x + offset_x,
            y=piece.y + offset_y,
        )
        if can_place(state.board, candidate):
            return _after_player_transform(state, candidate, "rotated")
    return Transition(state)


def soft_drop(state: GameState) -> Transition:
    if state.status != "running":
        return Transition(state)
    lowered = replace(state.active, y=state.active.y + 1)
    if not can_place(state.board, lowered):
        return Transition(state)
    return Transition(
        replace(
            state,
            active=lowered,
            score=state.score + 1,
            gravity_elapsed_ms=0.0,
            lock_elapsed_ms=0.0,
        ),
        ("moved",),
        drop_distance=1,
        gained_score=1,
    )


def _clear_lines(board: Board) -> tuple[Board, tuple[int, ...]]:
    cleared = tuple(index for index, row in enumerate(board) if all(row))
    if not cleared:
        return board, ()
    remaining = tuple(row for index, row in enumerate(board) if index not in cleared)
    empty = tuple(tuple(0 for _ in range(BOARD_WIDTH)) for _ in cleared)
    return empty + remaining, cleared


def _line_score(count: int, level: int) -> int:
    return (0, 100, 300, 500, 800)[count] * level


def _spawn_next(state: GameState, rng=None) -> GameState:
    queue, bag = _refill_queue(state.next_queue, state.bag, NEXT_COUNT + 1, rng)
    active = ActivePiece(queue[0])
    queue, bag = _refill_queue(queue[1:], bag, NEXT_COUNT, rng)
    spawned = replace(
        state,
        active=active,
        next_queue=queue,
        bag=bag,
        hold_used=False,
        gravity_elapsed_ms=0.0,
        lock_elapsed_ms=0.0,
        lock_resets=0,
    )
    if not can_place(spawned.board, active):
        return replace(spawned, status="game_over")
    return spawned


def lock_piece(state: GameState, rng=None) -> Transition:
    if state.status != "running":
        return Transition(state)
    mutable = [list(row) for row in state.board]
    piece_id = PIECE_IDS[state.active.kind]
    for column, row in active_cells(state):
        if 0 <= row < BOARD_HEIGHT and 0 <= column < BOARD_WIDTH:
            mutable[row][column] = piece_id
    locked_board = tuple(tuple(row) for row in mutable)
    cleared_board, cleared_rows = _clear_lines(locked_board)
    count = len(cleared_rows)
    combo = state.combo + 1 if count else -1
    line_score = _line_score(count, state.level)
    combo_score = 50 * combo * state.level if count and combo > 0 else 0
    gained = line_score + combo_score
    total_lines = state.lines + count
    level = total_lines // 10 + 1
    locked = replace(
        state,
        board=cleared_board,
        score=state.score + gained,
        lines=total_lines,
        level=level,
        combo=combo,
    )
    spawned = _spawn_next(locked, rng)
    events: tuple[GameEvent, ...] = ("locked",)
    if cleared_rows:
        events += ("lines_cleared",)
    if spawned.status == "game_over":
        events += ("game_over",)
    return Transition(spawned, events, cleared_rows, gained_score=gained)


def hard_drop(state: GameState, rng=None) -> Transition:
    if state.status != "running":
        return Transition(state)
    target_y = ghost_y(state)
    distance = target_y - state.active.y
    dropped = replace(
        state,
        active=replace(state.active, y=target_y),
        score=state.score + distance * 2,
    )
    result = lock_piece(dropped, rng)
    return replace(
        result,
        drop_distance=distance,
        gained_score=result.gained_score + distance * 2,
    )


def hold_piece(state: GameState, rng=None) -> Transition:
    if state.status != "running" or state.hold_used:
        return Transition(state)
    current = state.active.kind
    if state.hold is None:
        queue, bag = _refill_queue(state.next_queue, state.bag, NEXT_COUNT + 1, rng)
        replacement = queue[0]
        queue, bag = _refill_queue(queue[1:], bag, NEXT_COUNT, rng)
    else:
        replacement = state.hold
        queue, bag = state.next_queue, state.bag
    held = replace(
        state,
        active=ActivePiece(replacement),
        next_queue=queue,
        bag=bag,
        hold=current,
        hold_used=True,
        gravity_elapsed_ms=0.0,
        lock_elapsed_ms=0.0,
        lock_resets=0,
    )
    if not can_place(held.board, held.active):
        held = replace(held, status="game_over")
        return Transition(held, ("held", "game_over"))
    return Transition(held, ("held",))


def advance_time(state: GameState, elapsed_ms: float, rng=None) -> Transition:
    """Advance gravity and lock delay by a deterministic amount of time."""

    if elapsed_ms < 0:
        raise ValueError("Elapsed time must not be negative.")
    if state.status != "running" or elapsed_ms == 0:
        return Transition(state)

    current = state
    gravity = current.gravity_elapsed_ms + elapsed_ms
    interval = gravity_interval_ms(current.level)
    events: list[GameEvent] = []
    while gravity >= interval:
        lowered = replace(current.active, y=current.active.y + 1)
        gravity -= interval
        if not can_place(current.board, lowered):
            gravity = 0.0
            break
        current = replace(
            current,
            active=lowered,
            lock_elapsed_ms=0.0,
        )
        events.append("moved")

    current = replace(current, gravity_elapsed_ms=gravity)
    if is_grounded(current):
        current = replace(current, lock_elapsed_ms=current.lock_elapsed_ms + elapsed_ms)
        if current.lock_elapsed_ms >= LOCK_DELAY_MS:
            result = lock_piece(current, rng)
            return replace(result, events=tuple(events) + result.events)
    elif current.lock_elapsed_ms:
        current = replace(current, lock_elapsed_ms=0.0)
    return Transition(current, tuple(events))


def toggle_pause(state: GameState) -> GameState:
    if state.status == "running":
        return replace(state, status="paused")
    if state.status == "paused":
        return replace(state, status="running")
    return state
