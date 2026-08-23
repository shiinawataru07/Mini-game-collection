"""Render deterministic Gomoku documentation screenshots."""

from __future__ import annotations

from pathlib import Path

import pygame
from games.game_gomoku.logic import GameState, new_game, place_stone
from games.game_gomoku.ui import draw_game

WINDOW_SIZE = (760, 820)
OUTPUT_DIRECTORY = Path(__file__).parents[1] / "docs" / "images" / "gomoku"
DEMO_MOVES = (
    (7, 7),
    (7, 8),
    (8, 7),
    (6, 7),
    (8, 8),
    (6, 8),
    (9, 7),
    (5, 7),
    (9, 8),
    (5, 8),
)


def play(state: GameState, moves: tuple[tuple[int, int], ...]) -> GameState:
    for move in moves:
        result = place_stone(state, move)
        if not result.placed:
            raise RuntimeError(f"Could not render illegal demonstration move: {move}")
        state = result.state
    return state


def render(name: str, state: GameState, **options: object) -> None:
    surface = pygame.Surface(WINDOW_SIZE)
    draw_game(surface, state, **options)
    pygame.image.save(surface, OUTPUT_DIRECTORY / name)


def main() -> None:
    pygame.font.init()
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    render("gameplay.png", play(new_game("local"), DEMO_MOVES))
    render(
        "mode-selection.png",
        new_game("local"),
        mode_selecting=True,
        ai_difficulty="normal",
    )
    render(
        "ai-gameplay.png",
        play(new_game("ai"), DEMO_MOVES[:-1]),
        ai_thinking=True,
        ai_difficulty="expert",
    )


if __name__ == "__main__":
    main()
