"""Declarative registry for every game exposed by the collection menu."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import cast

import pygame

from games.common.types import Navigation
from games.game_2048.preview import draw_preview as draw_2048_preview
from games.game_gomoku.preview import draw_preview as draw_gomoku_preview
from games.game_minesweeper.preview import draw_preview as draw_minesweeper_preview
from games.game_snake.preview import draw_preview as draw_snake_preview
from games.game_tetris.preview import draw_preview as draw_tetris_preview

GameRunner = Callable[[], Navigation]
PreviewRenderer = Callable[[pygame.Surface, pygame.Rect], None]


@dataclass(frozen=True)
class GameDescriptor:
    id: str
    title: str
    subtitle: str
    shortcut: int
    accent: tuple[int, int, int]
    runner: str
    preview: PreviewRenderer

    def load_runner(self) -> GameRunner:
        """Load the game only when it is selected from the menu."""

        module_name, function_name = self.runner.split(":", maxsplit=1)
        function = getattr(import_module(module_name), function_name)
        if not callable(function):
            raise TypeError(f"Registered game runner is not callable: {self.runner}")
        return cast(GameRunner, function)


GAMES: tuple[GameDescriptor, ...] = (
    GameDescriptor(
        id="2048",
        title="2048",
        subtitle="数字合并 · 策略",
        shortcut=1,
        accent=(238, 177, 76),
        runner="games.game_2048.game:run",
        preview=draw_2048_preview,
    ),
    GameDescriptor(
        id="snake",
        title="贪吃蛇",
        subtitle="移动成长 · 反应",
        shortcut=2,
        accent=(79, 151, 81),
        runner="games.game_snake.game:run",
        preview=draw_snake_preview,
    ),
    GameDescriptor(
        id="minesweeper",
        title="扫雷",
        subtitle="逻辑排雷 · 推理",
        shortcut=3,
        accent=(49, 110, 184),
        runner="games.game_minesweeper.game:run",
        preview=draw_minesweeper_preview,
    ),
    GameDescriptor(
        id="tetris",
        title="俄罗斯方块",
        subtitle="堆叠消行 · 反应",
        shortcut=4,
        accent=(139, 116, 255),
        runner="games.game_tetris.game:run",
        preview=draw_tetris_preview,
    ),
    GameDescriptor(
        id="gomoku",
        title="五子棋",
        subtitle="连珠成五 · 对弈",
        shortcut=5,
        accent=(150, 96, 52),
        runner="games.game_gomoku.game:run",
        preview=draw_gomoku_preview,
    ),
)


def _validate_registry(games: tuple[GameDescriptor, ...]) -> None:
    ids = [game.id for game in games]
    shortcuts = [game.shortcut for game in games]
    if len(ids) != len(set(ids)):
        raise ValueError("Game IDs must be unique")
    if len(shortcuts) != len(set(shortcuts)):
        raise ValueError("Game shortcuts must be unique")
    if any(":" not in game.runner for game in games):
        raise ValueError("Game runners must use the 'module:function' format")


_validate_registry(GAMES)
GAMES_BY_ID = {game.id: game for game in GAMES}
GAMES_BY_SHORTCUT = {game.shortcut: game for game in GAMES}


def game_by_id(game_id: str) -> GameDescriptor:
    try:
        return GAMES_BY_ID[game_id]
    except KeyError as error:
        raise ValueError(f"Unknown game: {game_id}") from error


def game_by_shortcut(shortcut: int) -> GameDescriptor | None:
    return GAMES_BY_SHORTCUT.get(shortcut)
