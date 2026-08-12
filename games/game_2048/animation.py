"""Pygame-independent movement and tile-effect animation models."""

from __future__ import annotations

from dataclasses import dataclass

from .logic import Board, Direction, GameState, apply_move, move_board


@dataclass(frozen=True)
class TileMotion:
    value: int
    start: tuple[int, int]
    end: tuple[int, int]


@dataclass(frozen=True)
class MoveAnimation:
    start_state: GameState
    end_state: GameState
    motions: list[TileMotion]
    merged_positions: frozenset[tuple[int, int]]
    spawned_position: tuple[int, int] | None
    gained_score: int
    started_at: int


@dataclass(frozen=True)
class ScorePopup:
    amount: int
    started_at: int


def _line_coordinates(
    dimension: int, direction: Direction, line_index: int
) -> list[tuple[int, int]]:
    if direction == "left":
        return [(line_index, column) for column in range(dimension)]
    if direction == "right":
        return [(line_index, column) for column in range(dimension - 1, -1, -1)]
    if direction == "up":
        return [(row, line_index) for row in range(dimension)]
    return [(row, line_index) for row in range(dimension - 1, -1, -1)]


def build_tile_motions(board: Board, direction: Direction) -> list[TileMotion]:
    """Map every existing tile to its destination for a move animation."""

    dimension = len(board)
    motions: list[TileMotion] = []
    for line_index in range(dimension):
        coordinates = _line_coordinates(dimension, direction, line_index)
        sources = [
            (position, board[position[0]][position[1]])
            for position in coordinates
            if board[position[0]][position[1]]
        ]
        source_index = 0
        target_index = 0
        while source_index < len(sources):
            start, value = sources[source_index]
            destination = coordinates[target_index]
            motions.append(TileMotion(value, start, destination))
            if (
                source_index + 1 < len(sources)
                and value == sources[source_index + 1][1]
            ):
                second_start, second_value = sources[source_index + 1]
                motions.append(TileMotion(second_value, second_start, destination))
                source_index += 2
            else:
                source_index += 1
            target_index += 1
    return motions


def build_move_animation(
    state: GameState,
    direction: Direction,
    started_at: int,
    rng=None,
) -> MoveAnimation | None:
    """Build all visual information for one valid move."""

    if state.game_over:
        return None

    moved_board, gained_score, changed = move_board(state.board, direction)
    if not changed:
        return None

    end_state = apply_move(state, direction, rng)
    motions = build_tile_motions(state.board, direction)
    destination_counts: dict[tuple[int, int], int] = {}
    for motion in motions:
        destination_counts[motion.end] = destination_counts.get(motion.end, 0) + 1

    merged_positions = frozenset(
        position for position, count in destination_counts.items() if count == 2
    )
    spawned_position = next(
        (
            (row, column)
            for row in range(len(moved_board))
            for column in range(len(moved_board))
            if moved_board[row][column] == 0 and end_state.board[row][column] != 0
        ),
        None,
    )
    return MoveAnimation(
        start_state=state,
        end_state=end_state,
        motions=motions,
        merged_positions=merged_positions,
        spawned_position=spawned_position,
        gained_score=gained_score,
        started_at=started_at,
    )


def merge_pop_scale(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    if progress <= 0.5:
        return 1.0 + 0.15 * (progress / 0.5)
    return 1.15 - 0.15 * ((progress - 0.5) / 0.5)


def spawn_pop_scale(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    if progress <= 0.7:
        return 1.1 * (1 - (1 - progress / 0.7) ** 3)
    return 1.1 - 0.1 * ((progress - 0.7) / 0.3)


def animation_tile_scales(
    animation: MoveAnimation, progress: float
) -> dict[tuple[int, int], float]:
    scales = {
        position: merge_pop_scale(progress)
        for position in animation.merged_positions
    }
    if animation.spawned_position is not None:
        scales[animation.spawned_position] = spawn_pop_scale(progress)
    return scales

