"""Mutable search position derived from the immutable rules state."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..config import BOARD_SIZE
from ..logic import DIRECTIONS, GameState, Position
from .zobrist import SIDE_KEY, STONE_KEYS, hash_board


@dataclass
class SearchPosition:
    board: list[list[int]]
    current_player: int
    moves: list[Position]
    hash_key: int
    analysis_cache: dict[tuple[int, Position, int], object] = field(
        default_factory=dict,
        compare=False,
        repr=False,
    )

    @classmethod
    def from_state(cls, state: GameState) -> SearchPosition:
        board = [list(row) for row in state.board]
        return cls(
            board, state.current_player, list(state.moves), hash_board(board, state.current_player)
        )

    def make_move(self, move: Position) -> None:
        row, column = move
        if not self.is_legal(move):
            raise ValueError(f"Illegal search move: {move}")
        player = self.current_player
        self.board[row][column] = player
        self.hash_key ^= STONE_KEYS[row][column][player - 1]
        self.hash_key ^= SIDE_KEY
        self.moves.append(move)
        self.current_player = 3 - player

    def unmake_move(self) -> Position:
        if not self.moves:
            raise ValueError("Cannot unmake an empty position")
        move = self.moves.pop()
        row, column = move
        player = 3 - self.current_player
        self.current_player = player
        self.hash_key ^= SIDE_KEY
        self.hash_key ^= STONE_KEYS[row][column][player - 1]
        self.board[row][column] = 0
        return move

    def is_legal(self, move: Position) -> bool:
        row, column = move
        return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE and self.board[row][column] == 0

    def is_win_at(self, move: Position, player: int | None = None) -> bool:
        row, column = move
        stone = self.board[row][column] if player is None else player
        if stone == 0:
            return False
        for delta_row, delta_column in DIRECTIONS:
            total = 1
            for sign in (-1, 1):
                step = 1
                while True:
                    target_row = row + delta_row * step * sign
                    target_column = column + delta_column * step * sign
                    if not (
                        0 <= target_row < BOARD_SIZE
                        and 0 <= target_column < BOARD_SIZE
                        and self.board[target_row][target_column] == stone
                    ):
                        break
                    total += 1
                    step += 1
            if total >= 5:
                return True
        return False

    def is_winning_move(self, move: Position, player: int) -> bool:
        """Check a virtual move without mutating the position."""

        if not self.is_legal(move):
            return False
        row, column = move
        self.board[row][column] = player
        try:
            return self.is_win_at(move, player)
        finally:
            self.board[row][column] = 0
