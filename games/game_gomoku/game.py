"""Gomoku application loop coordinating mode selection, rules, and UI."""

from __future__ import annotations

import pygame

from games.common.app_settings import handle_global_shortcut, load_app_settings
from games.common.types import Navigation
from games.common.window import open_resizable_window, resize_resizable_window

from .config import (
    FPS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .logic import new_game, place_stone, undo
from .sound import GameSounds
from .ui import draw_game, mode_controls, page_layout, position_at_point


def run() -> Navigation:
    """Run the local two-player Gomoku MVP."""

    app_settings = load_app_settings()
    screen = open_resizable_window(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        "Mini Game Collection - Gomoku",
        app_settings.fullscreen,
    )
    clock = pygame.time.Clock()
    sounds = GameSounds(app_settings)
    state = new_game("local")
    mode_selecting = True
    mode_closable = False
    mode_notice = ""
    navigation: Navigation = "menu"
    running = True

    def start_local_game() -> None:
        nonlocal mode_closable, mode_notice, mode_selecting, state
        state = new_game("local")
        mode_selecting = False
        mode_closable = True
        mode_notice = ""

    def request_ai_mode() -> None:
        nonlocal mode_notice
        mode_notice = "人机模式入口已保留，AI 将在下一阶段实现"

    def undo_move() -> None:
        nonlocal state
        previous = state
        state = undo(state)
        if state != previous:
            sounds.play_undo()

    while running:
        layout = draw_game(
            screen,
            state,
            mode_selecting,
            mode_notice,
            mode_closable,
        )
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                navigation = "quit"
                running = False
                continue
            if event.type == pygame.VIDEORESIZE:
                screen = resize_resizable_window(
                    (event.w, event.h),
                    (MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT),
                )
                continue
            if event.type == pygame.KEYDOWN:
                handled = handle_global_shortcut(
                    event.key,
                    app_settings,
                    (MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT),
                )
                if handled is not None:
                    app_settings, screen = handled
                    sounds.update_settings(app_settings)
                elif event.key == pygame.K_ESCAPE:
                    if mode_selecting and mode_closable:
                        mode_selecting = False
                        mode_notice = ""
                    else:
                        running = False
                elif mode_selecting and event.key in (pygame.K_1, pygame.K_KP1):
                    start_local_game()
                elif mode_selecting and event.key in (pygame.K_2, pygame.K_KP2):
                    request_ai_mode()
                elif not mode_selecting and event.key == pygame.K_r:
                    state = new_game(state.mode)
                elif not mode_selecting and event.key in (pygame.K_u, pygame.K_BACKSPACE):
                    undo_move()
                continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue
            if mode_selecting:
                controls = mode_controls(screen.get_size())
                if mode_closable and controls.close.collidepoint(event.pos):
                    mode_selecting = False
                    mode_notice = ""
                elif controls.local.collidepoint(event.pos):
                    start_local_game()
                elif controls.ai.collidepoint(event.pos):
                    request_ai_mode()
                continue

            layout = page_layout(screen.get_size())
            if layout.back.collidepoint(event.pos):
                running = False
            elif layout.mode.collidepoint(event.pos):
                mode_selecting = True
                mode_closable = True
                mode_notice = ""
            elif layout.undo.collidepoint(event.pos):
                undo_move()
            elif layout.restart.collidepoint(event.pos):
                state = new_game(state.mode)
            elif state.status == "playing":
                position = position_at_point(layout, event.pos)
                if position is not None:
                    result = place_stone(state, position)
                    state = result.state
                    sounds.play_move(result)

        clock.tick(FPS)

    return navigation
