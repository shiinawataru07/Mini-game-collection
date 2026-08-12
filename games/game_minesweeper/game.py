"""Minesweeper application loop coordinating input, rules, UI, and storage."""

from __future__ import annotations

from typing import cast

import pygame

from games.common.types import Navigation
from games.common.window import open_resizable_window, resize_resizable_window

from .config import (
    DEFAULT_DIFFICULTY,
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    DIFFICULTY_ORDER,
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
    normalize_custom_spec,
)
from .input import BoardMouseInput, MouseAction
from .logic import (
    advance_time,
    chord_cell,
    cycle_mark,
    new_custom_game,
    new_game,
    reveal_cell,
)
from .persistence import PlayerData, load_player_data, save_player_data, update_best_time
from .solver import Hint, find_hint
from .sound import GameSounds, play_outcome_transition
from .ui import cell_at_position, draw_game, page_layout, settings_controls

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
    sounds = GameSounds()
    player_data = load_player_data()
    theme_name = player_data.theme if player_data.theme in THEMES else DEFAULT_THEME
    language = cast(
        Language, player_data.language if player_data.language in TEXTS else DEFAULT_LANGUAGE
    )
    difficulty = cast(
        Difficulty,
        player_data.difficulty
        if player_data.difficulty in DIFFICULTY_ORDER
        else DEFAULT_DIFFICULTY,
    )
    custom_spec = normalize_custom_spec(
        player_data.custom_width,
        player_data.custom_height,
        player_data.custom_mines,
    )
    best_times = dict(player_data.best_times_ms)

    def create_state(selected: Difficulty):
        if selected == "custom":
            return new_custom_game(custom_spec.width, custom_spec.height, custom_spec.mines)
        return new_game(selected)

    state = create_state(difficulty)
    settings_open = False
    active_hint: Hint | None = None
    hint_message_key: str | None = None
    hint_remaining_ms = 0
    navigation: Navigation = "menu"
    running = True
    mouse_input = BoardMouseInput()

    def persist() -> None:
        save_player_data(
            PlayerData(
                dict(best_times),
                theme_name,
                language,
                difficulty,
                custom_spec.width,
                custom_spec.height,
                custom_spec.mines,
            )
        )

    def choose_difficulty(selected: Difficulty) -> None:
        nonlocal active_hint, difficulty, hint_message_key, hint_remaining_ms, state
        difficulty = selected
        state = create_state(difficulty)
        active_hint = None
        hint_message_key = None
        hint_remaining_ms = 0
        mouse_input.reset()

    def adjust_custom(field: str, direction: int) -> None:
        nonlocal custom_spec
        values = {
            "width": custom_spec.width,
            "height": custom_spec.height,
            "mines": custom_spec.mines,
        }
        values[field] += direction
        custom_spec = normalize_custom_spec(values["width"], values["height"], values["mines"])
        choose_difficulty("custom")

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
        if difficulty == "custom":
            return
        data = PlayerData(
            dict(best_times),
            theme_name,
            language,
            difficulty,
            custom_spec.width,
            custom_spec.height,
            custom_spec.mines,
        )
        best_times = dict(update_best_time(data, difficulty, state.elapsed_ms).best_times_ms)
        persist()

    def finish_board_action(previous_status: str) -> None:
        play_outcome_transition(previous_status, state.status, sounds)
        record_win(previous_status)

    def apply_mouse_action(action: MouseAction, position: tuple[int, int]) -> None:
        nonlocal state
        previous_status = state.status
        if action == "reveal":
            cell = state.board[position[0]][position[1]]
            if cell.visibility != "revealed":
                state = reveal_cell(state, position).state
        elif action == "mark":
            state = cycle_mark(state, position)
        else:
            state = chord_cell(state, position).state
        finish_board_action(previous_status)

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
                mouse_input.reset()
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
                    state = create_state(difficulty)
                    settings_open = False
                    clear_hint()
                    mouse_input.reset()
                elif event.key == pygame.K_s:
                    settings_open = not settings_open
                    mouse_input.reset()
                elif event.key == pygame.K_h and not settings_open:
                    request_hint()
                elif not settings_open and event.key in DIFFICULTY_KEYS:
                    choose_difficulty(DIFFICULTY_KEYS[event.key])
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and settings_open:
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
                for field, rect in controls.custom_decrease.items():
                    if rect.collidepoint(event.pos):
                        adjust_custom(field, -1)
                        break
                for field, rect in controls.custom_increase.items():
                    if rect.collidepoint(event.pos):
                        adjust_custom(field, 1)
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

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and layout.back.collidepoint(event.pos):
                    running = False
                    mouse_input.reset()
                elif event.button == 1 and layout.settings.collidepoint(event.pos):
                    settings_open = True
                    mouse_input.reset()
                elif event.button == 1 and layout.hint.collidepoint(event.pos):
                    request_hint()
                elif event.button == 1 and layout.restart.collidepoint(event.pos):
                    state = create_state(difficulty)
                    clear_hint()
                    mouse_input.reset()
                elif event.button in (1, 3):
                    position = cell_at_position(layout, event.pos)
                    if position is None:
                        continue
                    clear_hint()
                    cell = state.board[position[0]][position[1]]
                    action = mouse_input.press(
                        event.button,
                        position,
                        cell.visibility == "revealed" and cell.adjacent_mines > 0,
                    )
                    if action is not None:
                        apply_mouse_action(action, position)
                continue

            if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                position = cell_at_position(layout, event.pos)
                action = mouse_input.release(event.button, position)
                if action is not None and position is not None:
                    clear_hint()
                    apply_mouse_action(action, position)

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
                custom_spec,
            )
            pygame.display.flip()

    persist()
    return navigation
