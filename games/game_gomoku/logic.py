"""Pure Gomoku rules with immutable state and no Pygame dependency."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .config import BOARD_SIZE

Player = Literal[1, 2]
GameMode = Literal["local", "ai"]
GameStatus = Literal["playing", "black_won", "white_won", "draw"]
Position = tuple[int, int]
Board = tuple[tuple[int, ...], ...]

DIRECTIONS: tuple[Position, ...] = ((1, 0), (0, 1), (1, 1), (1, -1))


@dataclass(frozen=True)
class GameState:
    board: Board
    current_player: Player = 1
    status: GameStatus = "playing"
    mode: GameMode = "local"
    moves: tuple[Position, ...] = ()
    winning_line: tuple[Position, ...] = ()


@dataclass(frozen=True)
class MoveResult:
    state: GameState
    placed: bool = False
    won: bool = False
    draw: bool = False


def empty_board() -> Board:
    return tuple(tuple(0 for _ in range(BOARD_SIZE)) for _ in range(BOARD_SIZE))


def new_game(mode: GameMode = "local") -> GameState:
    if mode not in ("local", "ai"):
        raise ValueError(f"Unsupported Gomoku mode: {mode}")
    return GameState(empty_board(), mode=mode)


def _inside(position: Position) -> bool:
    row, column = position
    return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE


def winning_line(board: Board, position: Position) -> tuple[Position, ...]:
    """Return the complete contiguous winning line through the latest stone."""

    if not _inside(position):
        return ()
    row, column = position
    player = board[row][column]
    if player == 0:
        return ()
    for delta_row, delta_column in DIRECTIONS:
        line: list[Position] = [position]
        for sign in (-1, 1):
            step = 1
            while True:
                candidate = (
                    row + delta_row * step * sign,
                    column + delta_column * step * sign,
                )
                if not _inside(candidate) or board[candidate[0]][candidate[1]] != player:
                    break
                if sign < 0:
                    line.insert(0, candidate)
                else:
                    line.append(candidate)
                step += 1
        if len(line) >= 5:
            return tuple(line)
    return ()


def place_stone(state: GameState, position: Position) -> MoveResult:
    if state.status != "playing" or not _inside(position):
        return MoveResult(state)
    row, column = position
    if state.board[row][column] != 0:
        return MoveResult(state)

    mutable = [list(board_row) for board_row in state.board]
    mutable[row][column] = state.current_player
    board = tuple(tuple(board_row) for board_row in mutable)
    line = winning_line(board, position)
    moves = state.moves + (position,)
    if line:
        status: GameStatus = "black_won" if state.current_player == 1 else "white_won"
        return MoveResult(
            GameState(board, state.current_player, status, state.mode, moves, line),
            placed=True,
            won=True,
        )
    if len(moves) == BOARD_SIZE * BOARD_SIZE:
        return MoveResult(
            GameState(board, state.current_player, "draw", state.mode, moves),
            placed=True,
            draw=True,
        )
    next_player: Player = 2 if state.current_player == 1 else 1
    return MoveResult(
        GameState(board, next_player, "playing", state.mode, moves),
        placed=True,
    )


def undo(state: GameState) -> GameState:
    """Undo one local move, or a human/AI pair once AI mode is implemented."""

    if not state.moves:
        return state
    remove_count = 2 if state.mode == "ai" and len(state.moves) >= 2 else 1
    remaining = state.moves[:-remove_count]
    mutable = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for index, (row, column) in enumerate(remaining):
        mutable[row][column] = 1 if index % 2 == 0 else 2
    current_player: Player = 1 if len(remaining) % 2 == 0 else 2
    return GameState(
        tuple(tuple(row) for row in mutable),
        current_player,
        "playing",
        state.mode,
        remaining,
    )
