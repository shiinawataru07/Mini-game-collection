"""Pure Snake rules with no dependency on Pygame or persistence."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import Literal

from .config import FOOD_SCORE, GRID_HEIGHT, GRID_WIDTH, INITIAL_SNAKE_LENGTH

Cell = tuple[int, int]
Direction = Literal["up", "down", "left", "right"]
GameStatus = Literal["ready", "running", "paused", "game_over", "won"]
GameMode = Literal["classic", "wrap"]
Collision = Literal["wall", "self"]

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


@dataclass(frozen=True)
class StepResult:
    state: GameState
    ate_food: bool = False
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
) -> Cell | None:
    """Choose an empty cell uniformly, or return None when the board is full."""

    rng = rng or random
    occupied = set(snake)
    available = [
        (column, row)
        for row in range(height)
        for column in range(width)
        if (column, row) not in occupied
    ]
    return rng.choice(available) if available else None


def new_game(
    width: int = GRID_WIDTH,
    height: int = GRID_HEIGHT,
    mode: GameMode = "classic",
    rng=None,
) -> GameState:
    if width < INITIAL_SNAKE_LENGTH + 1 or height < 3:
        raise ValueError("The Snake board is too small.")
    if mode not in ("classic", "wrap"):
        raise ValueError(f"Unsupported Snake mode: {mode}")

    head_x = width // 2
    head_y = height // 2
    snake = tuple((head_x - offset, head_y) for offset in range(INITIAL_SNAKE_LENGTH))
    return GameState(
        width=width,
        height=height,
        snake=snake,
        direction="right",
        food=spawn_food(width, height, snake, rng),
        mode=mode,
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


def advance(state: GameState, rng=None) -> StepResult:
    """Advance one simulation tick and return the resulting immutable state."""

    if state.status != "running":
        return StepResult(state)

    new_head = next_head(state.snake[0], state.direction)
    outside = not (0 <= new_head[0] < state.width and 0 <= new_head[1] < state.height)
    if outside:
        if state.mode == "classic":
            return StepResult(replace(state, status="game_over"), collision="wall")
        new_head = (new_head[0] % state.width, new_head[1] % state.height)

    ate_food = new_head == state.food
    body_to_check = state.snake if ate_food else state.snake[:-1]
    if new_head in body_to_check:
        return StepResult(replace(state, status="game_over"), collision="self")

    if ate_food:
        new_snake = (new_head,) + state.snake
        new_score = state.score + FOOD_SCORE
        food = spawn_food(state.width, state.height, new_snake, rng)
        status: GameStatus = "won" if food is None else "running"
    else:
        new_snake = (new_head,) + state.snake[:-1]
        new_score = state.score
        food = state.food
        status = "running"

    return StepResult(
        GameState(
            width=state.width,
            height=state.height,
            snake=new_snake,
            direction=state.direction,
            food=food,
            score=new_score,
            status=status,
            steps=state.steps + 1,
            mode=state.mode,
        ),
        ate_food=ate_food,
    )
