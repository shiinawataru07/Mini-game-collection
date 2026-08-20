"""Tetris application loop coordinating input, rules, UI, and storage."""

from __future__ import annotations

import random
from typing import cast

import pygame

from games.common.app_settings import handle_global_shortcut, load_app_settings
from games.common.types import Navigation
from games.common.window import open_resizable_window, resize_resizable_window

from .animation import LineClearAnimation, animation_from_transition
from .config import (
    ARR_MS,
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    FPS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    TEXTS,
    THEMES,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Language,
)
from .input import HorizontalDirection, HorizontalInput
from .logic import (
    Transition,
    advance_time,
    hard_drop,
    hold_piece,
    move,
    new_game,
    rotate,
    soft_drop,
    toggle_pause,
)
from .persistence import PlayerData, load_player_data, save_player_data
from .sound import GameSounds
from .ui import draw_game, settings_controls

HORIZONTAL_KEYS: dict[int, HorizontalDirection] = {
    pygame.K_LEFT: "left",
    pygame.K_a: "left",
    pygame.K_RIGHT: "right",
    pygame.K_d: "right",
}
SOFT_DROP_KEYS = (pygame.K_DOWN, pygame.K_s)


def run() -> Navigation:
    """Run Tetris until the player returns to the collection or quits."""

    app_settings = load_app_settings()
    screen = open_resizable_window(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        "Mini Game Collection - Tetris",
        app_settings.fullscreen,
    )
    clock = pygame.time.Clock()
    sounds = GameSounds(app_settings)
    rng = random.Random()
    player_data = load_player_data()
    best_score = player_data.best_score
    best_lines = player_data.best_lines
    theme_name = player_data.theme if player_data.theme in THEMES else DEFAULT_THEME
    language = cast(
        Language, player_data.language if player_data.language in TEXTS else DEFAULT_LANGUAGE
    )
    state = new_game(rng)
    horizontal = HorizontalInput()
    soft_drop_held = False
    soft_drop_elapsed = 0.0
    settings_open = False
    resume_after_settings = False
    animation: LineClearAnimation | None = None
    navigation: Navigation = "menu"
    running = True

    def persist() -> None:
        save_player_data(PlayerData(best_score, best_lines, theme_name, language))

    def reset_inputs() -> None:
        nonlocal soft_drop_elapsed, soft_drop_held
        horizontal.reset()
        soft_drop_held = False
        soft_drop_elapsed = 0.0

    def apply_transition(transition: Transition, now: int) -> None:
        nonlocal animation, best_lines, best_score, state
        state = transition.state
        sounds.play_transition(transition)
        if transition.cleared_rows:
            animation = animation_from_transition(transition, now)
        changed_record = False
        if state.score > best_score:
            best_score = state.score
            changed_record = True
        if state.lines > best_lines:
            best_lines = state.lines
            changed_record = True
        if changed_record or "game_over" in transition.events:
            persist()

    def restart() -> None:
        nonlocal animation, settings_open, state
        state = new_game(rng)
        animation = None
        settings_open = False
        reset_inputs()

    def set_settings(opened: bool) -> None:
        nonlocal resume_after_settings, settings_open, state
        if opened:
            resume_after_settings = state.status == "running"
            if resume_after_settings:
                state = toggle_pause(state)
            settings_open = True
            reset_inputs()
        else:
            settings_open = False
            if resume_after_settings and state.status == "paused":
                state = toggle_pause(state)
            resume_after_settings = False

    def horizontal_move(direction: HorizontalDirection, now: int) -> None:
        apply_transition(move(state, -1 if direction == "left" else 1), now)

    while running:
        elapsed_ms = min(clock.tick(FPS), 250)
        now = pygame.time.get_ticks()
        if animation is not None and animation.finished(now):
            animation = None

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
            if event.type == pygame.KEYUP:
                if event.key in HORIZONTAL_KEYS:
                    fallback = horizontal.release(HORIZONTAL_KEYS[event.key])
                    if fallback is not None and state.status == "running" and not settings_open:
                        horizontal_move(fallback, now)
                elif event.key in SOFT_DROP_KEYS:
                    soft_drop_held = False
                    soft_drop_elapsed = 0.0
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
                    if settings_open:
                        set_settings(False)
                    else:
                        running = False
                elif event.key == pygame.K_r:
                    restart()
                elif event.key == pygame.K_p and not settings_open:
                    state = toggle_pause(state)
                    reset_inputs()
                elif (
                    event.key in HORIZONTAL_KEYS and state.status == "running" and not settings_open
                ):
                    direction = horizontal.press(HORIZONTAL_KEYS[event.key])
                    if direction is not None:
                        horizontal_move(direction, now)
                elif (
                    event.key in SOFT_DROP_KEYS and state.status == "running" and not settings_open
                ):
                    if not soft_drop_held:
                        soft_drop_held = True
                        soft_drop_elapsed = 0.0
                        apply_transition(soft_drop(state), now)
                elif event.key in (pygame.K_UP, pygame.K_x, pygame.K_w) and not settings_open:
                    apply_transition(rotate(state, "clockwise"), now)
                elif event.key == pygame.K_z and not settings_open:
                    apply_transition(rotate(state, "counterclockwise"), now)
                elif event.key == pygame.K_SPACE and not settings_open:
                    apply_transition(hard_drop(state, rng), now)
                elif (
                    event.key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT)
                    and not settings_open
                ):
                    apply_transition(hold_piece(state, rng), now)
                continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue
            if settings_open:
                controls = settings_controls(screen.get_size())
                if controls.close.collidepoint(event.pos):
                    set_settings(False)
                else:
                    for selected, rect in controls.themes.items():
                        if rect.collidepoint(event.pos):
                            theme_name = selected
                            persist()
                            break
                    for selected_language, rect in controls.languages.items():
                        if rect.collidepoint(event.pos):
                            language = selected_language
                            persist()
                            break
                continue

            layout = draw_game(screen, state, best_score, theme_name, language)
            if layout.back.collidepoint(event.pos):
                running = False
            elif layout.pause.collidepoint(event.pos):
                state = toggle_pause(state)
                reset_inputs()
            elif layout.restart.collidepoint(event.pos):
                restart()
            elif layout.settings.collidepoint(event.pos):
                set_settings(True)

        if not running:
            continue

        if state.status == "running" and not settings_open:
            for direction in horizontal.advance(elapsed_ms):
                horizontal_move(direction, now)
            if soft_drop_held:
                soft_drop_elapsed += elapsed_ms
                while soft_drop_elapsed >= ARR_MS:
                    soft_drop_elapsed -= ARR_MS
                    apply_transition(soft_drop(state), now)
            apply_transition(advance_time(state, elapsed_ms, rng), now)

        draw_game(
            screen,
            state,
            best_score,
            theme_name,
            language,
            settings_open,
            animation,
            now,
        )
        pygame.display.flip()

    persist()
    return navigation
