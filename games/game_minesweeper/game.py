"""Minesweeper application loop coordinating input, rules, UI, and storage."""

from __future__ import annotations

from typing import Literal, cast

import pygame

from games.common.window import open_resizable_window, resize_resizable_window

from .config import (
    DEFAULT_DIFFICULTY,
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    DIFFICULTIES,
    FPS,
    HINT_DISPLAY_MS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    TEXTS,
    THEMES,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Difficulty,
    Language,
)
from .logic import advance_time, cycle_mark, new_game, reveal_cell
from .persistence import PlayerData, load_player_data, save_player_data, update_best_time
from .solver import Hint, find_hint
from .ui import cell_at_position, draw_game, page_layout, settings_controls

Navigation = Literal["menu", "quit"]

DIFFICULTY_KEYS: dict[int, Difficulty] = {
    pygame.K_1: "beginner",
    pygame.K_KP1: "beginner",
    pygame.K_2: "intermediate",
    pygame.K_KP2: "intermediate",
    pygame.K_3: "expert",
    pygame.K_KP3: "expert",
}


def run() -> Navigation:
    """Run Minesweeper until the player returns to the collection or quits."""

    screen = open_resizable_window(
        (WINDOW_WIDTH, WINDOW_HEIGHT), "Mini Game Collection - Minesweeper"
    )
    clock = pygame.time.Clock()
    player_data = load_player_data()
    theme_name = player_data.theme if player_data.theme in THEMES else DEFAULT_THEME
    language = cast(
        Language, player_data.language if player_data.language in TEXTS else DEFAULT_LANGUAGE
    )
    difficulty = cast(
        Difficulty,
        player_data.difficulty if player_data.difficulty in DIFFICULTIES else DEFAULT_DIFFICULTY,
    )
    best_times = dict(player_data.best_times_ms)
    state = new_game(difficulty)
    settings_open = False
    active_hint: Hint | None = None
    hint_message_key: str | None = None
    hint_remaining_ms = 0
    navigation: Navigation = "menu"
    running = True

    def persist() -> None:
        save_player_data(PlayerData(dict(best_times), theme_name, language, difficulty))

    def choose_difficulty(selected: Difficulty) -> None:
        nonlocal active_hint, difficulty, hint_message_key, hint_remaining_ms, state
        difficulty = selected
        state = new_game(difficulty)
        active_hint = None
        hint_message_key = None
        hint_remaining_ms = 0

    def clear_hint() -> None:
        nonlocal active_hint, hint_message_key, hint_remaining_ms
        active_hint = None
        hint_message_key = None
        hint_remaining_ms = 0

    def request_hint() -> None:
        nonlocal active_hint, hint_message_key, hint_remaining_ms
        active_hint = find_hint(state)
        hint_message_key = f"hint_{active_hint.kind}" if active_hint is not None else "hint_none"
        hint_remaining_ms = HINT_DISPLAY_MS

    def record_win(previous_status: str) -> None:
        nonlocal best_times
        if previous_status == "won" or state.status != "won":
            return
        data = PlayerData(dict(best_times), theme_name, language, difficulty)
        best_times = dict(update_best_time(data, difficulty, state.elapsed_ms).best_times_ms)
        persist()

    while running:
        elapsed_ms = clock.tick(FPS)
        was_timing = state.status == "running" and not settings_open
        layout = page_layout(screen.get_size(), (state.width, state.height))

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
                elif event.key == pygame.K_r:
                    state = new_game(difficulty)
                    settings_open = False
                    clear_hint()
                elif event.key == pygame.K_s:
                    settings_open = not settings_open
                elif event.key == pygame.K_h and not settings_open:
                    request_hint()
                elif not settings_open and event.key in DIFFICULTY_KEYS:
                    choose_difficulty(DIFFICULTY_KEYS[event.key])
                continue
            if event.type != pygame.MOUSEBUTTONDOWN:
                continue

            if settings_open:
                if event.button != 1:
                    continue
                controls = settings_controls(screen.get_size())
                if controls.close.collidepoint(event.pos):
                    settings_open = False
                    continue
                for selected, rect in controls.difficulties.items():
                    if rect.collidepoint(event.pos):
                        choose_difficulty(selected)
                        break
                for selected, rect in controls.themes.items():
                    if rect.collidepoint(event.pos):
                        theme_name = selected
                        break
                for selected, rect in controls.languages.items():
                    if rect.collidepoint(event.pos):
                        language = selected
                        break
                persist()
                continue

            if event.button == 1 and layout.back.collidepoint(event.pos):
                running = False
            elif event.button == 1 and layout.settings.collidepoint(event.pos):
                settings_open = True
            elif event.button == 1 and layout.hint.collidepoint(event.pos):
                request_hint()
            elif event.button == 1 and layout.restart.collidepoint(event.pos):
                state = new_game(difficulty)
                clear_hint()
            elif event.button in (1, 3):
                position = cell_at_position(layout, event.pos)
                if position is None:
                    continue
                clear_hint()
                previous_status = state.status
                if event.button == 1:
                    state = reveal_cell(state, position).state
                    record_win(previous_status)
                else:
                    state = cycle_mark(state, position)

        if was_timing and state.status == "running" and not settings_open:
            state = advance_time(state, elapsed_ms)
        if hint_remaining_ms > 0:
            hint_remaining_ms = max(0, hint_remaining_ms - elapsed_ms)
            if hint_remaining_ms == 0:
                clear_hint()
        if running:
            draw_game(
                screen,
                state,
                best_times,
                theme_name,
                language,
                settings_open,
                active_hint,
                hint_message_key,
            )
            pygame.display.flip()

    persist()
    return navigation
