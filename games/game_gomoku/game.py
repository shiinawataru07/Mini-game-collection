"""Gomoku application loop coordinating mode selection, rules, and UI."""

from __future__ import annotations

import pygame

from games.common.app_settings import handle_global_shortcut, load_app_settings
from games.common.types import Navigation
from games.common.window import open_resizable_window, resize_resizable_window

from .ai import Difficulty, limits_for_difficulty
from .ai.controller import AIController
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
    """Run local and search-based AI Gomoku modes."""

    app_settings = load_app_settings()
    screen = open_resizable_window(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        "Mini Game Collection - Gomoku",
        app_settings.fullscreen,
    )
    clock = pygame.time.Clock()
    sounds = GameSounds(app_settings)
    ai = AIController()
    state = new_game("local")
    mode_selecting = True
    mode_closable = False
    mode_notice = ""
    navigation: Navigation = "menu"
    running = True
    ai_difficulty: Difficulty = "normal"

    def start_local_game() -> None:
        nonlocal mode_closable, mode_notice, mode_selecting, state
        ai.cancel()
        state = new_game("local")
        mode_selecting = False
        mode_closable = True
        mode_notice = ""

    def request_ai_mode(difficulty: Difficulty | None = None) -> None:
        nonlocal ai_difficulty, mode_closable, mode_notice, mode_selecting, state
        ai.cancel()
        if difficulty is not None:
            ai_difficulty = difficulty
        state = new_game("ai")
        mode_selecting = False
        mode_closable = True
        mode_notice = ""

    def undo_move() -> None:
        nonlocal state
        ai.cancel()
        previous = state
        state = undo(state)
        if state != previous:
            sounds.play_undo()

    def restart_game() -> None:
        nonlocal state
        ai.cancel()
        state = new_game(state.mode)

    def start_ai_turn() -> None:
        if (
            state.mode == "ai"
            and state.status == "playing"
            and state.current_player == 2
            and not ai.thinking
        ):
            ai.start(state, limits_for_difficulty(ai_difficulty))

    while running:
        completion = ai.poll()
        if (
            completion is not None
            and completion.source_moves == state.moves
            and state.mode == "ai"
            and state.status == "playing"
            and state.current_player == 2
            and completion.result.move is not None
        ):
            result = place_stone(state, completion.result.move)
            state = result.state
            sounds.play_move(result)

        layout = draw_game(
            screen,
            state,
            mode_selecting,
            mode_notice,
            mode_closable,
            ai.thinking,
            ai_difficulty,
        )
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ai.cancel()
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
                    request_ai_mode("easy")
                elif mode_selecting and event.key in (pygame.K_3, pygame.K_KP3):
                    request_ai_mode("normal")
                elif mode_selecting and event.key in (pygame.K_4, pygame.K_KP4):
                    request_ai_mode("expert")
                elif not mode_selecting and event.key == pygame.K_r:
                    restart_game()
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
                elif controls.easy.collidepoint(event.pos):
                    request_ai_mode("easy")
                elif controls.normal.collidepoint(event.pos):
                    request_ai_mode("normal")
                elif controls.expert.collidepoint(event.pos):
                    request_ai_mode("expert")
                elif controls.ai.collidepoint(event.pos):
                    request_ai_mode()
                continue

            layout = page_layout(screen.get_size())
            if layout.back.collidepoint(event.pos):
                ai.cancel()
                running = False
            elif layout.mode.collidepoint(event.pos):
                mode_selecting = True
                mode_closable = True
                mode_notice = ""
            elif layout.undo.collidepoint(event.pos):
                undo_move()
            elif layout.restart.collidepoint(event.pos):
                restart_game()
            elif state.status == "playing" and not ai.thinking:
                position = position_at_point(layout, event.pos)
                human_turn = state.mode == "local" or state.current_player == 1
                if position is not None and human_turn:
                    result = place_stone(state, position)
                    state = result.state
                    sounds.play_move(result)
                    if result.placed:
                        start_ai_turn()

        clock.tick(FPS)

    ai.close()
    return navigation
