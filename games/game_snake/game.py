"""Snake application loop coordinating input, fixed-step rules, UI, and storage."""

from __future__ import annotations

from collections import deque
from typing import cast

import pygame

from games.common.types import Navigation
from games.common.window import open_resizable_window, resize_resizable_window

from .config import (
    DEFAULT_LANGUAGE,
    DEFAULT_SPEED,
    DEFAULT_THEME,
    FPS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    SPEEDS,
    TEXTS,
    THEMES,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Language,
    Speed,
    move_interval_ms,
)
from .logic import (
    Direction,
    GameMode,
    advance,
    change_direction,
    elapse_bonus_timer,
    new_game,
    start_or_turn,
    toggle_pause,
)
from .persistence import load_player_data, save_player_data
from .ui import draw_game, mode_controls, settings_controls

KEY_DIRECTIONS: dict[int, Direction] = {
    pygame.K_UP: "up",
    pygame.K_w: "up",
    pygame.K_DOWN: "down",
    pygame.K_s: "down",
    pygame.K_LEFT: "left",
    pygame.K_a: "left",
    pygame.K_RIGHT: "right",
    pygame.K_d: "right",
}


def run() -> Navigation:
    """Run Snake until the player returns to the collection menu or quits."""

    screen = open_resizable_window((WINDOW_WIDTH, WINDOW_HEIGHT), "Mini Game Collection - Snake")
    clock = pygame.time.Clock()

    player_data = load_player_data()
    best_score = player_data.best_score
    theme_name = player_data.theme if player_data.theme in THEMES else DEFAULT_THEME
    language = cast(
        Language, player_data.language if player_data.language in TEXTS else DEFAULT_LANGUAGE
    )
    speed = cast(Speed, player_data.speed if player_data.speed in SPEEDS else DEFAULT_SPEED)
    state = new_game()
    pending_directions: deque[Direction] = deque(maxlen=2)
    accumulator = 0.0
    settings_open = False
    mode_selecting = True
    navigation: Navigation = "menu"
    running = True

    while running:
        elapsed_ms = clock.tick(FPS)
        simulation_elapsed_ms = min(elapsed_ms, 250)
        layout = draw_game(
            screen,
            state,
            best_score,
            theme_name,
            language,
            speed,
            settings_open,
            mode_selecting,
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
                if event.key == pygame.K_ESCAPE:
                    if settings_open:
                        settings_open = False
                    else:
                        running = False
                elif mode_selecting and event.key in (
                    pygame.K_1,
                    pygame.K_KP1,
                    pygame.K_2,
                    pygame.K_KP2,
                    pygame.K_3,
                    pygame.K_KP3,
                ):
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        mode: GameMode = "classic"
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        mode = "wrap"
                    else:
                        mode = "maze"
                    state = new_game(state.width, state.height, mode)
                    mode_selecting = False
                    accumulator = 0.0
                elif mode_selecting or settings_open:
                    continue
                elif event.key == pygame.K_r:
                    mode_selecting = True
                    pending_directions.clear()
                    accumulator = 0.0
                elif event.key in (pygame.K_SPACE, pygame.K_p):
                    state = toggle_pause(state)
                    settings_open = False
                    accumulator = 0.0
                elif event.key == pygame.K_s and state.status == "paused":
                    settings_open = True
                elif event.key in KEY_DIRECTIONS and state.status in ("ready", "running"):
                    requested = KEY_DIRECTIONS[event.key]
                    basis = pending_directions[-1] if pending_directions else state.direction
                    accepted = change_direction(basis, requested)
                    if accepted != requested:
                        continue
                    if state.status == "ready":
                        state = start_or_turn(state, accepted)
                        accumulator = 0.0
                    elif accepted != basis and len(pending_directions) < pending_directions.maxlen:
                        pending_directions.append(accepted)
                continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if mode_selecting:
                controls = mode_controls(screen.get_size())
                selected_mode: GameMode | None = None
                if controls.classic.collidepoint(event.pos):
                    selected_mode = "classic"
                elif controls.wrap.collidepoint(event.pos):
                    selected_mode = "wrap"
                elif controls.maze.collidepoint(event.pos):
                    selected_mode = "maze"
                if selected_mode is not None:
                    state = new_game(state.width, state.height, selected_mode)
                    mode_selecting = False
                    accumulator = 0.0
                continue

            if settings_open:
                controls = settings_controls(screen.get_size())
                if controls.close.collidepoint(event.pos):
                    settings_open = False
                else:
                    for name, rect in controls.themes.items():
                        if rect.collidepoint(event.pos):
                            theme_name = name
                            break
                    for selected_language, rect in controls.languages.items():
                        if rect.collidepoint(event.pos):
                            language = selected_language
                            break
                    for selected_speed, rect in controls.speeds.items():
                        if rect.collidepoint(event.pos):
                            speed = selected_speed
                            break
                continue

            if layout.back.collidepoint(event.pos):
                running = False
            elif layout.restart.collidepoint(event.pos):
                mode_selecting = True
                pending_directions.clear()
                accumulator = 0.0
            elif layout.pause.collidepoint(event.pos):
                state = toggle_pause(state)
                accumulator = 0.0
            elif layout.settings.collidepoint(event.pos) and state.status == "paused":
                settings_open = True

        if not running:
            continue

        if state.status == "running":
            state = elapse_bonus_timer(state, elapsed_ms)
            accumulator += simulation_elapsed_ms
            interval = move_interval_ms(speed)
            while accumulator >= interval and state.status == "running":
                accumulator -= interval
                if pending_directions:
                    state = start_or_turn(state, pending_directions.popleft())
                result = advance(state)
                state = result.state
                if state.score > best_score:
                    best_score = state.score
                    save_player_data(best_score, theme_name, language, speed=speed)
                interval = move_interval_ms(speed)
        else:
            accumulator = 0.0

    save_player_data(best_score, theme_name, language, speed=speed)
    return navigation
