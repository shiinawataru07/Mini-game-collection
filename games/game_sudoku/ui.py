"""Responsive Pygame layout and rendering for Sudoku."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from games.common.controls import draw_button, draw_overlay, draw_panel
from games.common.fonts import get_font
from games.common.types import Language

from .config import THEMES, Theme, text
from .logic import GameState, Position, conflicting_positions, is_given, wrong_positions
from .puzzles import DIFFICULTY_ORDER, Difficulty, level_count, level_key


@dataclass(frozen=True)
class Layout:
    board: pygame.Rect
    back: pygame.Rect
    levels: pygame.Rect
    settings: pygame.Rect
    restart: pygame.Rect
    stats: tuple[pygame.Rect, ...]
    numbers: dict[int, pygame.Rect]
    undo: pygame.Rect
    redo: pygame.Rect
    erase: pygame.Rect
    notes: pygame.Rect
    hint: pygame.Rect
    pause: pygame.Rect
    cell_size: int


@dataclass(frozen=True)
class SettingsControls:
    modal: pygame.Rect
    close: pygame.Rect
    themes: dict[str, pygame.Rect]
    languages: dict[Language, pygame.Rect]


@dataclass(frozen=True)
class LevelControls:
    modal: pygame.Rect
    difficulties: dict[Difficulty, pygame.Rect]
    levels: dict[int, pygame.Rect]


def page_layout(window_size: tuple[int, int]) -> Layout:
    width, height = window_size
    margin = max(14, min(22, width // 34))
    button_width = max(70, min(88, (width - margin * 2 - 190) // 4))
    button_height = 34
    back = pygame.Rect(margin, 18, button_width, button_height)
    levels = pygame.Rect(back.right + 8, 18, button_width, button_height)
    restart = pygame.Rect(width - margin - button_width, 18, button_width, button_height)
    settings = pygame.Rect(restart.left - 8 - button_width, 18, button_width, button_height)

    stat_gap = 8
    stat_width = max(92, min(142, (width - margin * 2 - stat_gap * 3) // 4))
    stats_width = stat_width * 4 + stat_gap * 3
    stats_left = (width - stats_width) // 2
    stats = tuple(
        pygame.Rect(stats_left + index * (stat_width + stat_gap), 68, stat_width, 44)
        for index in range(4)
    )

    cell_size = max(40, min(66, (width - margin * 2) // 9, (height - 255) // 9))
    board = pygame.Rect(0, 0, cell_size * 9, cell_size * 9)
    board.midtop = (width // 2, 126)

    number_y = board.bottom + 13
    numbers = {
        value: pygame.Rect(
            board.left + (value - 1) * cell_size + 2,
            number_y,
            cell_size - 4,
            40,
        )
        for value in range(1, 10)
    }
    action_y = number_y + 49
    action_gap = 7
    action_width = (board.width - action_gap * 5) // 6
    actions = tuple(
        pygame.Rect(board.left + index * (action_width + action_gap), action_y, action_width, 38)
        for index in range(6)
    )
    return Layout(
        board,
        back,
        levels,
        settings,
        restart,
        stats,
        numbers,
        *actions,
        cell_size,
    )


def settings_controls(window_size: tuple[int, int]) -> SettingsControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(500, width - 36), min(350, height - 36))
    modal.center = (width // 2, height // 2)
    close = pygame.Rect(modal.right - 92, modal.top + 18, 70, 34)
    left = modal.left + 30
    content_width = modal.width - 60
    gap = 10
    theme_width = (content_width - gap * 2) // 3
    themes = {
        name: pygame.Rect(left + index * (theme_width + gap), modal.top + 115, theme_width, 45)
        for index, name in enumerate(THEMES)
    }
    language_width = (content_width - gap) // 2
    languages: dict[Language, pygame.Rect] = {
        "zh": pygame.Rect(left, modal.top + 245, language_width, 45),
        "en": pygame.Rect(left + language_width + gap, modal.top + 245, language_width, 45),
    }
    return SettingsControls(modal, close, themes, languages)


def level_controls(window_size: tuple[int, int]) -> LevelControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(680, width - 32), min(600, height - 32))
    modal.center = (width // 2, height // 2)
    left = modal.left + 28
    content_width = modal.width - 56
    gap = 10
    difficulty_width = (content_width - gap * 2) // 3
    difficulties = {
        difficulty: pygame.Rect(
            left + index * (difficulty_width + gap),
            modal.top + 80,
            difficulty_width,
            42,
        )
        for index, difficulty in enumerate(DIFFICULTY_ORDER)
    }
    columns = 5
    card_gap = 10
    card_width = (content_width - card_gap * (columns - 1)) // columns
    card_height = min(76, (modal.height - 188 - card_gap * 3) // 4)
    levels = {
        index: pygame.Rect(
            left + index % columns * (card_width + card_gap),
            modal.top + 146 + index // columns * (card_height + card_gap),
            card_width,
            card_height,
        )
        for index in range(20)
    }
    return LevelControls(modal, difficulties, levels)


def cell_at_position(layout: Layout, position: tuple[int, int]) -> Position | None:
    if not layout.board.collidepoint(position):
        return None
    return (
        (position[1] - layout.board.top) // layout.cell_size,
        (position[0] - layout.board.left) // layout.cell_size,
    )


def format_time(milliseconds: int | None) -> str:
    if milliseconds is None:
        return "--:--"
    seconds = max(0, milliseconds // 1000)
    minutes, seconds = divmod(seconds, 60)
    return f"{min(99, minutes):02d}:{seconds:02d}"


def _font(size: int, language: Language = "zh", bold: bool = False):
    return get_font(size, language, bold, minimum_size=11)


def _button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    theme: Theme,
    language: Language,
    active: bool = False,
) -> None:
    draw_button(
        screen,
        rect,
        label,
        theme.accent if active else theme.panel,
        theme.panel if active else theme.text,
        15,
        language,
        border_color=theme.grid,
        border_radius=9,
        minimum_font_size=11,
    )


def _draw_stat(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    value: str,
    theme: Theme,
    language: Language,
) -> None:
    draw_panel(screen, rect, theme.panel, border_color=theme.grid, border_radius=9)
    label_surface = _font(12, language).render(label, True, theme.muted_text)
    value_surface = _font(18, language, True).render(value, True, theme.text)
    screen.blit(label_surface, label_surface.get_rect(midtop=(rect.centerx, rect.top + 3)))
    screen.blit(value_surface, value_surface.get_rect(midbottom=(rect.centerx, rect.bottom - 3)))


def _cell_rect(layout: Layout, position: Position) -> pygame.Rect:
    row, column = position
    return pygame.Rect(
        layout.board.left + column * layout.cell_size,
        layout.board.top + row * layout.cell_size,
        layout.cell_size,
        layout.cell_size,
    )


def _is_related(first: Position, second: Position) -> bool:
    return (
        first[0] == second[0]
        or first[1] == second[1]
        or (first[0] // 3, first[1] // 3) == (second[0] // 3, second[1] // 3)
    )


def _draw_board(
    screen: pygame.Surface,
    state: GameState,
    layout: Layout,
    theme: Theme,
    language: Language,
) -> None:
    conflicts = conflicting_positions(state)
    wrong = wrong_positions(state)
    selected_value = (
        state.values[state.selected[0]][state.selected[1]] if state.selected is not None else 0
    )
    for row in range(9):
        for column in range(9):
            position = (row, column)
            rect = _cell_rect(layout, position)
            color = theme.alternate if (row // 3 + column // 3) % 2 else theme.board
            if state.selected is not None and _is_related(position, state.selected):
                color = theme.related
            if selected_value and state.values[row][column] == selected_value:
                color = theme.related
            if position == state.selected:
                color = theme.selected
            if position in conflicts or position in wrong:
                color = tuple(
                    round(channel * 0.62 + error * 0.38)
                    for channel, error in zip(color, theme.error, strict=True)
                )
            pygame.draw.rect(screen, color, rect)
            value = state.values[row][column]
            if value:
                number_color = theme.error if position in conflicts or position in wrong else (
                    theme.given if is_given(state, position) else theme.entry
                )
                number = _font(
                    max(22, round(layout.cell_size * 0.54)), "en", is_given(state, position)
                ).render(str(value), True, number_color)
                screen.blit(number, number.get_rect(center=rect.center))
            else:
                note_font = _font(max(10, layout.cell_size // 5), "en", True)
                for note in state.notes[row][column]:
                    note_row, note_column = divmod(note - 1, 3)
                    center = (
                        rect.left + round((note_column + 0.5) * rect.width / 3),
                        rect.top + round((note_row + 0.5) * rect.height / 3),
                    )
                    rendered = note_font.render(str(note), True, theme.note)
                    screen.blit(rendered, rendered.get_rect(center=center))

    for index in range(10):
        width = 3 if index % 3 == 0 else 1
        color = theme.box_grid if width == 3 else theme.grid
        x = layout.board.left + index * layout.cell_size
        y = layout.board.top + index * layout.cell_size
        pygame.draw.line(screen, color, (x, layout.board.top), (x, layout.board.bottom), width)
        pygame.draw.line(screen, color, (layout.board.left, y), (layout.board.right, y), width)


def _draw_settings(
    screen: pygame.Surface,
    theme_name: str,
    language: Language,
) -> None:
    theme = THEMES[theme_name]
    controls = settings_controls(screen.get_size())
    draw_overlay(screen, theme.overlay, 175)
    draw_panel(screen, controls.modal, theme.panel, border_color=theme.grid, border_radius=16)
    title = _font(27, language, True).render(
        text(language, "settings_title"), True, theme.text
    )
    screen.blit(title, (controls.modal.left + 28, controls.modal.top + 22))
    _button(screen, controls.close, text(language, "close"), theme, language)

    theme_label = _font(16, language, True).render(text(language, "theme"), True, theme.muted_text)
    screen.blit(theme_label, (controls.modal.left + 30, controls.modal.top + 82))
    for name, rect in controls.themes.items():
        _button(screen, rect, text(language, name), theme, language, name == theme_name)

    language_label = _font(16, language, True).render(
        text(language, "language"), True, theme.muted_text
    )
    screen.blit(language_label, (controls.modal.left + 30, controls.modal.top + 212))
    for selected, rect in controls.languages.items():
        key = "chinese" if selected == "zh" else "english"
        _button(screen, rect, text(language, key), theme, language, selected == language)


def _draw_level_selection(
    screen: pygame.Surface,
    selector_difficulty: Difficulty,
    current_level: tuple[Difficulty, int],
    best_times_ms: dict[str, int],
    theme_name: str,
    language: Language,
) -> None:
    theme = THEMES[theme_name]
    controls = level_controls(screen.get_size())
    draw_overlay(screen, theme.overlay, 185)
    draw_panel(screen, controls.modal, theme.panel, border_color=theme.grid, border_radius=16)
    heading = _font(28, language, True).render(
        text(language, "choose_level"), True, theme.text
    )
    screen.blit(heading, heading.get_rect(midtop=(controls.modal.centerx, controls.modal.top + 24)))
    for difficulty, rect in controls.difficulties.items():
        _button(
            screen,
            rect,
            text(language, difficulty),
            theme,
            language,
            difficulty == selector_difficulty,
        )
    for index, rect in controls.levels.items():
        key = level_key(selector_difficulty, index)
        completed = key in best_times_ms
        active = current_level == (selector_difficulty, index)
        background = theme.selected if active else theme.board
        draw_panel(
            screen,
            rect,
            background,
            border_color=theme.success if completed else theme.grid,
            border_width=2 if active or completed else 1,
            border_radius=10,
        )
        number = _font(20, "en", True).render(str(index + 1), True, theme.text)
        screen.blit(number, number.get_rect(center=(rect.centerx, rect.top + rect.height // 3)))
        status = format_time(best_times_ms[key]) if completed else "· · ·"
        status_color = theme.success if completed else theme.muted_text
        rendered = _font(12, "en", completed).render(status, True, status_color)
        screen.blit(rendered, rendered.get_rect(center=(rect.centerx, rect.bottom - rect.height // 4)))


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    best_times_ms: dict[str, int],
    theme_name: str,
    language: Language,
    *,
    settings_open: bool = False,
    level_selecting: bool = False,
    selector_difficulty: Difficulty = "easy",
) -> Layout:
    theme = THEMES[theme_name]
    layout = page_layout(screen.get_size())
    screen.fill(theme.background)
    title = _font(30, language, True).render(text(language, "title"), True, theme.text)
    screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 35)))
    _button(screen, layout.back, text(language, "back"), theme, language)
    _button(screen, layout.levels, text(language, "levels"), theme, language, level_selecting)
    _button(screen, layout.settings, text(language, "settings"), theme, language, settings_open)
    _button(screen, layout.restart, text(language, "restart"), theme, language)

    stat_values = (
        (text(language, "difficulty"), text(language, state.difficulty)),
        (text(language, "level"), f"{state.level.number}/{level_count(state.difficulty)}"),
        (text(language, "time"), format_time(state.elapsed_ms)),
        (text(language, "mistakes"), str(state.mistakes)),
    )
    for rect, (label, value) in zip(layout.stats, stat_values, strict=True):
        _draw_stat(screen, rect, label, value, theme, language)

    _draw_board(screen, state, layout, theme, language)
    for value, rect in layout.numbers.items():
        _button(screen, rect, str(value), theme, "en")
    action_labels = (
        (layout.undo, "undo", False),
        (layout.redo, "redo", False),
        (layout.erase, "erase", False),
        (layout.notes, "note", state.note_mode),
        (layout.hint, "hint_button", False),
        (layout.pause, "resume" if state.status == "paused" else "pause", False),
    )
    for rect, key, active in action_labels:
        _button(screen, rect, text(language, key), theme, language, active)

    hint = _font(13, language).render(text(language, "hint"), True, theme.muted_text)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 14)))

    if state.status in ("paused", "won") and not settings_open and not level_selecting:
        draw_overlay(screen, theme.overlay, 185, layout.board)
        key = "paused" if state.status == "paused" else "won"
        label = _font(34, language, True).render(text(language, key), True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=(layout.board.centerx, layout.board.centery - 16)))
        if state.status == "won":
            subtitle = _font(15, language).render(
                text(language, "won_hint"), True, (232, 238, 236)
            )
            screen.blit(
                subtitle,
                subtitle.get_rect(center=(layout.board.centerx, layout.board.centery + 28)),
            )

    if settings_open:
        _draw_settings(screen, theme_name, language)
    elif level_selecting:
        _draw_level_selection(
            screen,
            selector_difficulty,
            (state.difficulty, state.level.index),
            best_times_ms,
            theme_name,
            language,
        )
    return layout
