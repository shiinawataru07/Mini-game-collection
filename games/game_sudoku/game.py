"""Sudoku application loop coordinating input, UI, sound, and progress."""

from __future__ import annotations

from typing import cast

import pygame

from games.common.app_settings import handle_global_shortcut, load_app_settings
from games.common.types import Language, Navigation
from games.common.window import open_resizable_window, resize_resizable_window

from .config import (
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    FPS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    TEXTS,
    THEMES,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .logic import (
    Transition,
    advance_time,
    apply_hint,
    clear_selected,
    move_selection,
    new_game,
    redo,
    select_cell,
    set_value,
    toggle_note_mode,
    toggle_pause,
    undo,
)
from .persistence import PlayerData, load_player_data, record_completion, save_player_data
from .puzzles import Difficulty
from .sound import GameSounds
from .ui import (
    cell_at_position,
    draw_game,
    level_controls,
    page_layout,
    settings_controls,
)

DIGIT_KEYS: dict[int, int] = {
    **{getattr(pygame, f"K_{value}"): value for value in range(1, 10)},
    **{getattr(pygame, f"K_KP{value}"): value for value in range(1, 10)},
}


def run() -> Navigation:
    """Run Sudoku until the player returns to the collection or quits."""

    app_settings = load_app_settings()
    screen = open_resizable_window(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        "Mini Game Collection - Sudoku",
        app_settings.fullscreen,
    )
    clock = pygame.time.Clock()
    sounds = GameSounds(app_settings)
    player_data = load_player_data()
    theme_name = player_data.theme if player_data.theme in THEMES else DEFAULT_THEME
    language = cast(
        Language, player_data.language if player_data.language in TEXTS else DEFAULT_LANGUAGE
    )
    best_times = dict(player_data.best_times_ms)
    state = new_game(player_data.difficulty, player_data.level_index)
    selector_difficulty = player_data.difficulty
    level_selecting = True
    settings_open = False
    navigation: Navigation = "menu"
    running = True

    def persist() -> None:
        save_player_data(
            PlayerData(
                best_times_ms=dict(best_times),
                theme=theme_name,
                language=language,
                difficulty=state.difficulty,
                level_index=state.level.index,
            )
        )

    def choose_level(difficulty: Difficulty, index: int) -> None:
        nonlocal level_selecting, selector_difficulty, settings_open, state
        selector_difficulty = difficulty
        state = new_game(difficulty, index)
        level_selecting = False
        settings_open = False
        persist()

    def apply_transition(transition: Transition) -> None:
        nonlocal best_times, state
        state = transition.state
        sounds.play_transition(transition)
        if "won" in transition.events:
            data = PlayerData(
                best_times_ms=dict(best_times),
                theme=theme_name,
                language=language,
                difficulty=state.difficulty,
                level_index=state.level.index,
            )
            best_times = dict(
                record_completion(
                    data,
                    state.difficulty,
                    state.level.index,
                    state.elapsed_ms,
                ).best_times_ms
            )
            persist()

    while running:
        elapsed_ms = min(clock.tick(FPS), 250)
        layout = page_layout(screen.get_size())
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
                    if settings_open:
                        settings_open = False
                    elif level_selecting:
                        level_selecting = False
                    else:
                        running = False
                elif event.key == pygame.K_l and not settings_open:
                    selector_difficulty = state.difficulty
                    level_selecting = True
                elif event.key == pygame.K_s and not level_selecting:
                    settings_open = not settings_open
                elif event.key == pygame.K_r and not settings_open and not level_selecting:
                    state = new_game(state.difficulty, state.level.index)
                elif event.key in (pygame.K_p, pygame.K_SPACE) and not any(
                    (settings_open, level_selecting)
                ):
                    state = toggle_pause(state)
                elif level_selecting and event.key in (pygame.K_1, pygame.K_KP1):
                    selector_difficulty = "easy"
                elif level_selecting and event.key in (pygame.K_2, pygame.K_KP2):
                    selector_difficulty = "medium"
                elif level_selecting and event.key in (pygame.K_3, pygame.K_KP3):
                    selector_difficulty = "hard"
                elif not settings_open and not level_selecting:
                    modifiers = pygame.key.get_mods()
                    if event.key == pygame.K_z and modifiers & pygame.KMOD_CTRL:
                        apply_transition(undo(state))
                    elif event.key == pygame.K_y and modifiers & pygame.KMOD_CTRL:
                        apply_transition(redo(state))
                    elif event.key == pygame.K_n:
                        state = toggle_note_mode(state)
                    elif event.key == pygame.K_h:
                        apply_transition(apply_hint(state))
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_0, pygame.K_KP0):
                        apply_transition(clear_selected(state))
                    elif event.key in DIGIT_KEYS:
                        apply_transition(set_value(state, DIGIT_KEYS[event.key]))
                    elif event.key == pygame.K_UP:
                        state = move_selection(state, -1, 0)
                    elif event.key == pygame.K_DOWN:
                        state = move_selection(state, 1, 0)
                    elif event.key == pygame.K_LEFT:
                        state = move_selection(state, 0, -1)
                    elif event.key == pygame.K_RIGHT:
                        state = move_selection(state, 0, 1)
                continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue
            if settings_open:
                controls = settings_controls(screen.get_size())
                if controls.close.collidepoint(event.pos):
                    settings_open = False
                else:
                    for selected_theme, rect in controls.themes.items():
                        if rect.collidepoint(event.pos):
                            theme_name = selected_theme
                            persist()
                            break
                    for selected_language, rect in controls.languages.items():
                        if rect.collidepoint(event.pos):
                            language = selected_language
                            persist()
                            break
                continue
            if level_selecting:
                controls = level_controls(screen.get_size())
                changed_difficulty = False
                for difficulty, rect in controls.difficulties.items():
                    if rect.collidepoint(event.pos):
                        selector_difficulty = difficulty
                        changed_difficulty = True
                        break
                if not changed_difficulty:
                    for index, rect in controls.levels.items():
                        if rect.collidepoint(event.pos):
                            choose_level(selector_difficulty, index)
                            break
                continue

            if layout.back.collidepoint(event.pos):
                running = False
            elif layout.levels.collidepoint(event.pos):
                selector_difficulty = state.difficulty
                level_selecting = True
            elif layout.settings.collidepoint(event.pos):
                settings_open = True
            elif layout.restart.collidepoint(event.pos):
                state = new_game(state.difficulty, state.level.index)
            elif layout.undo.collidepoint(event.pos):
                apply_transition(undo(state))
            elif layout.redo.collidepoint(event.pos):
                apply_transition(redo(state))
            elif layout.erase.collidepoint(event.pos):
                apply_transition(clear_selected(state))
            elif layout.notes.collidepoint(event.pos):
                state = toggle_note_mode(state)
            elif layout.hint.collidepoint(event.pos):
                apply_transition(apply_hint(state))
            elif layout.pause.collidepoint(event.pos):
                state = toggle_pause(state)
            else:
                position = cell_at_position(layout, event.pos)
                if position is not None:
                    state = select_cell(state, position)
                else:
                    for value, rect in layout.numbers.items():
                        if rect.collidepoint(event.pos):
                            apply_transition(set_value(state, value))
                            break

        if state.status == "playing" and not settings_open and not level_selecting:
            state = advance_time(state, elapsed_ms)
        if running:
            draw_game(
                screen,
                state,
                best_times,
                theme_name,
                language,
                settings_open=settings_open,
                level_selecting=level_selecting,
                selector_difficulty=selector_difficulty,
            )
            pygame.display.flip()

    persist()
    return navigation
