"""Pure Snake rules with no dependency on Pygame or persistence."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import Literal

from .config import (
    BONUS_FOOD_DURATION_MS,
    BONUS_FOOD_EVERY,
    BONUS_FOOD_SCORE,
    FOOD_SCORE,
    GRID_HEIGHT,
    GRID_WIDTH,
    INITIAL_SNAKE_LENGTH,
)

Cell = tuple[int, int]
Direction = Literal["up", "down", "left", "right"]
GameStatus = Literal["ready", "running", "paused", "game_over", "won"]
GameMode = Literal["classic", "wrap", "maze"]
Collision = Literal["wall", "self", "obstacle"]

DIRECTION_VECTORS: dict[Direction, Cell] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

OPPOSITE_DIRECTIONS: dict[Direction, Direction] = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
}


@dataclass(frozen=True)
class GameState:
    width: int
    height: int
    snake: tuple[Cell, ...]
    direction: Direction
    food: Cell | None
    score: int = 0
    status: GameStatus = "ready"
    steps: int = 0
    mode: GameMode = "classic"
    walls: frozenset[Cell] = frozenset()
    bonus_food: Cell | None = None
    bonus_remaining_ms: float = 0.0
    foods_eaten: int = 0


@dataclass(frozen=True)
class StepResult:
    state: GameState
    ate_food: bool = False
    ate_bonus: bool = False
    collision: Collision | None = None


def change_direction(current: Direction, requested: Direction) -> Direction:
    """Accept a turn unless it immediately reverses the snake."""

    if current not in DIRECTION_VECTORS:
        raise ValueError(f"Unsupported current direction: {current}")
    if requested not in DIRECTION_VECTORS:
        raise ValueError(f"Unsupported requested direction: {requested}")
    if requested == OPPOSITE_DIRECTIONS[current]:
        return current
    return requested


def next_head(head: Cell, direction: Direction) -> Cell:
    if direction not in DIRECTION_VECTORS:
        raise ValueError(f"Unsupported direction: {direction}")
    delta_x, delta_y = DIRECTION_VECTORS[direction]
    return head[0] + delta_x, head[1] + delta_y


def spawn_food(
    width: int,
    height: int,
    snake: tuple[Cell, ...],
    rng=None,
    blocked: frozenset[Cell] = frozenset(),
    excluded: tuple[Cell, ...] = (),
) -> Cell | None:
    """Choose an empty cell uniformly, or return None when the board is full."""

    rng = rng or random
    occupied = set(snake) | set(blocked) | set(excluded)
    available = [
        (column, row)
        for row in range(height)
        for column in range(width)
        if (column, row) not in occupied
    ]
    return rng.choice(available) if available else None


def create_maze(width: int, height: int, snake: tuple[Cell, ...] = ()) -> frozenset[Cell]:
    """Build a connected, wide-corridor maze suited to a growing snake."""

    walls: set[Cell] = set()

    def vertical(x: int, start: int, end: int, gaps: set[int]) -> None:
        if 0 < x < width - 1:
            walls.update((x, row) for row in range(max(1, start), min(height - 1, end)) if row not in gaps)

    def horizontal(row: int, start: int, end: int, gaps: set[int]) -> None:
        if 0 < row < height - 1:
            walls.update((column, row) for column in range(max(1, start), min(width - 1, end)) if column not in gaps)

    if width == GRID_WIDTH and height == GRID_HEIGHT:
        vertical(4, 1, 14, {4, 9})
        vertical(11, 1, 8, {5})
        vertical(18, 2, 16, {6, 12})
        vertical(8, 11, 17, {14})
        vertical(15, 10, 17, {13})
        horizontal(3, 5, 11, {8})
        horizontal(7, 6, 18, {10, 14})
        horizontal(10, 16, 23, {20})
        horizontal(12, 1, 8, {4})
        horizontal(15, 9, 21, {13, 17})
    else:
        first_x = max(2, width // 3)
        second_x = min(width - 2, width * 2 // 3)
        vertical(first_x, 1, height - 2, {height // 2})
        vertical(second_x, 2, height - 1, {height // 3, height * 2 // 3})
        horizontal(height // 3, 1, width - 2, {first_x - 1, second_x + 1})
        horizontal(height * 2 // 3, 2, width - 1, {first_x + 1, second_x - 1})

    walls.difference_update(snake)
    return frozenset(walls)


def new_game(
    width: int = GRID_WIDTH,
    height: int = GRID_HEIGHT,
    mode: GameMode = "classic",
    rng=None,
) -> GameState:
    if width < INITIAL_SNAKE_LENGTH + 1 or height < 3:
        raise ValueError("The Snake board is too small.")
    if mode not in ("classic", "wrap", "maze"):
        raise ValueError(f"Unsupported Snake mode: {mode}")

    head_x = width // 2
    head_y = height // 2
    snake = tuple((head_x - offset, head_y) for offset in range(INITIAL_SNAKE_LENGTH))
    walls = create_maze(width, height, snake) if mode == "maze" else frozenset()
    return GameState(
        width=width,
        height=height,
        snake=snake,
        direction="right",
        food=spawn_food(width, height, snake, rng, walls),
        mode=mode,
        walls=walls,
    )


def start_or_turn(state: GameState, requested: Direction) -> GameState:
    """Apply a player direction and start a ready game on the first valid turn."""

    if state.status in ("game_over", "won"):
        return state
    direction = change_direction(state.direction, requested)
    status: GameStatus = "running" if state.status == "ready" else state.status
    return replace(state, direction=direction, status=status)


def toggle_pause(state: GameState) -> GameState:
    if state.status == "running":
        return replace(state, status="paused")
    if state.status == "paused":
        return replace(state, status="running")
    return state


def elapse_bonus_timer(state: GameState, elapsed_ms: float) -> GameState:
    """Advance the bonus timer only while gameplay is running."""

    if elapsed_ms < 0:
        raise ValueError("Elapsed time must not be negative.")
    if state.status != "running" or state.bonus_food is None:
        return state
    remaining = max(0.0, state.bonus_remaining_ms - elapsed_ms)
    if remaining == 0:
        return replace(state, bonus_food=None, bonus_remaining_ms=0.0)
    return replace(state, bonus_remaining_ms=remaining)


def advance(state: GameState, rng=None) -> StepResult:
    """Advance one simulation tick and return the resulting immutable state."""

    if state.status != "running":
        return StepResult(state)

    new_head = next_head(state.snake[0], state.direction)
    outside = not (0 <= new_head[0] < state.width and 0 <= new_head[1] < state.height)
    if outside:
        if state.mode == "classic":
            return StepResult(replace(state, status="game_over"), collision="wall")
        if state.mode == "wrap":
            new_head = (new_head[0] % state.width, new_head[1] % state.height)
        else:
            return StepResult(replace(state, status="game_over"), collision="wall")

    if new_head in state.walls:
        return StepResult(replace(state, status="game_over"), collision="obstacle")

    ate_food = new_head == state.food
    ate_bonus = new_head == state.bonus_food
    growing = ate_food or ate_bonus
    body_to_check = state.snake if growing else state.snake[:-1]
    if new_head in body_to_check:
        return StepResult(replace(state, status="game_over"), collision="self")

    if growing:
        new_snake = (new_head,) + state.snake
    else:
        new_snake = (new_head,) + state.snake[:-1]

    playable_cells = state.width * state.height - len(state.walls)
    if len(new_snake) >= playable_cells:
        return StepResult(
            replace(
                state,
                snake=new_snake,
                score=state.score + (FOOD_SCORE if ate_food else BONUS_FOOD_SCORE if ate_bonus else 0),
                status="won",
                steps=state.steps + 1,
                food=None,
                bonus_food=None,
                bonus_remaining_ms=0.0,
                foods_eaten=state.foods_eaten + (1 if ate_food else 0),
            ),
            ate_food=ate_food,
            ate_bonus=ate_bonus,
        )

    new_score = state.score
    food = state.food
    bonus_food = state.bonus_food
    bonus_remaining_ms = state.bonus_remaining_ms
    foods_eaten = state.foods_eaten

    if ate_food:
        new_score += FOOD_SCORE
        foods_eaten += 1
        food = spawn_food(
            state.width,
            state.height,
            new_snake,
            rng,
            state.walls,
            (bonus_food,) if bonus_food is not None else (),
        )
        if food is None and bonus_food is not None:
            bonus_food = None
            bonus_remaining_ms = 0.0
            food = spawn_food(state.width, state.height, new_snake, rng, state.walls)
        if foods_eaten % BONUS_FOOD_EVERY == 0:
            bonus_food = spawn_food(
                state.width,
                state.height,
                new_snake,
                rng,
                state.walls,
                (food,) if food is not None else (),
            )
            bonus_remaining_ms = BONUS_FOOD_DURATION_MS if bonus_food is not None else 0.0
    elif ate_bonus:
        new_score += BONUS_FOOD_SCORE
        bonus_food = None
        bonus_remaining_ms = 0.0

    return StepResult(
        GameState(
            width=state.width,
            height=state.height,
            snake=new_snake,
            direction=state.direction,
            food=food,
            score=new_score,
            status="running",
            steps=state.steps + 1,
            mode=state.mode,
            walls=state.walls,
            bonus_food=bonus_food,
            bonus_remaining_ms=bonus_remaining_ms,
            foods_eaten=foods_eaten,
        ),
        ate_food=ate_food,
        ate_bonus=ate_bonus,
    )
