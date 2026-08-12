"""Responsive layout and Pygame rendering for Minesweeper."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from games.common.controls import draw_button
from games.common.fonts import get_font

from .config import (
    DEFAULT_LANGUAGE,
    DIFFICULTY_ORDER,
    NUMBER_COLORS,
    THEMES,
    Difficulty,
    Language,
    Theme,
    text,
)
from .logic import GameState, Position, remaining_mines


@dataclass(frozen=True)
class Layout:
    board: pygame.Rect
    back: pygame.Rect
    settings: pygame.Rect
    restart: pygame.Rect
    mines: pygame.Rect
    timer: pygame.Rect
    best: pygame.Rect
    difficulty: pygame.Rect
    cell_size: int
    columns: int
    rows: int


@dataclass(frozen=True)
class SettingsControls:
    modal: pygame.Rect
    close: pygame.Rect
    difficulties: dict[Difficulty, pygame.Rect]
    themes: dict[str, pygame.Rect]
    languages: dict[Language, pygame.Rect]


def page_layout(window_size: tuple[int, int], grid_size: tuple[int, int]) -> Layout:
    """Return a centered board made from square integer-pixel cells."""

    width, height = window_size
    columns, rows = grid_size
    margin = max(12, min(24, min(width, height) // 24))
    header_bottom = 142
    footer_height = 46
    available_width = max(columns, width - margin * 2)
    available_height = max(rows, height - header_bottom - footer_height)
    cell_size = max(1, min(44, available_width // columns, available_height // rows))
    board_width = cell_size * columns
    board_height = cell_size * rows
    vertical_room = max(0, available_height - board_height)
    board = pygame.Rect(
        (width - board_width) // 2,
        header_bottom + vertical_room // 2,
        board_width,
        board_height,
    )

    button_width = max(72, min(94, width // 8))
    button_height = 36
    back = pygame.Rect(margin, 18, button_width, button_height)
    settings = pygame.Rect(back.right + 8, 18, button_width, button_height)
    restart = pygame.Rect(width - margin - button_width, 18, button_width, button_height)

    gap = 8
    card_width = max(82, min(142, (width - margin * 2 - gap * 3) // 4))
    cards_width = card_width * 4 + gap * 3
    cards_left = (width - cards_width) // 2
    card_y = 72
    mines = pygame.Rect(cards_left, card_y, card_width, 50)
    timer = pygame.Rect(mines.right + gap, card_y, card_width, 50)
    best = pygame.Rect(timer.right + gap, card_y, card_width, 50)
    difficulty = pygame.Rect(best.right + gap, card_y, card_width, 50)
    return Layout(
        board,
        back,
        settings,
        restart,
        mines,
        timer,
        best,
        difficulty,
        cell_size,
        columns,
        rows,
    )


def settings_controls(window_size: tuple[int, int]) -> SettingsControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(560, width - 36), min(460, height - 36))
    modal.center = (width // 2, height // 2)
    close = pygame.Rect(modal.right - 92, modal.top + 18, 70, 34)
    left = modal.left + 30
    content_width = modal.width - 60
    gap = 10

    difficulty_width = (content_width - gap * 2) // 3
    difficulties = {
        name: pygame.Rect(
            left + index * (difficulty_width + gap), modal.top + 100, difficulty_width, 48
        )
        for index, name in enumerate(DIFFICULTY_ORDER)
    }
    theme_width = (content_width - gap * 2) // 3
    themes = {
        name: pygame.Rect(left + index * (theme_width + gap), modal.top + 220, theme_width, 48)
        for index, name in enumerate(THEMES)
    }
    language_width = (content_width - gap) // 2
    languages: dict[Language, pygame.Rect] = {
        "zh": pygame.Rect(left, modal.top + 340, language_width, 48),
        "en": pygame.Rect(left + language_width + gap, modal.top + 340, language_width, 48),
    }
    return SettingsControls(modal, close, difficulties, themes, languages)


def cell_at_position(layout: Layout, position: tuple[int, int]) -> Position | None:
    if not layout.board.collidepoint(position):
        return None
    column = (position[0] - layout.board.left) // layout.cell_size
    row = (position[1] - layout.board.top) // layout.cell_size
    if row >= layout.rows or column >= layout.columns:
        return None
    return row, column


def _font(size: int, language: Language = DEFAULT_LANGUAGE, bold: bool = False):
    return get_font(size, language, bold, minimum_size=12)


def _draw_button(
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
        17,
        "zh" if any("\u3400" <= character <= "\u9fff" for character in label) else language,
        border_color=theme.grid,
        border_radius=9,
        minimum_font_size=12,
    )


def _draw_stat(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    value: str,
    theme: Theme,
    language: Language,
) -> None:
    pygame.draw.rect(screen, theme.panel, rect, border_radius=10)
    pygame.draw.rect(screen, theme.grid, rect, width=1, border_radius=10)
    label_surface = _font(13, language).render(label, True, theme.muted_text)
    value_surface = _font(20, language, True).render(value, True, theme.text)
    screen.blit(label_surface, label_surface.get_rect(midtop=(rect.centerx, rect.top + 4)))
    screen.blit(value_surface, value_surface.get_rect(midbottom=(rect.centerx, rect.bottom - 4)))


def _cell_rect(layout: Layout, position: Position) -> pygame.Rect:
    row, column = position
    return pygame.Rect(
        layout.board.left + column * layout.cell_size,
        layout.board.top + row * layout.cell_size,
        layout.cell_size,
        layout.cell_size,
    )


def _draw_flag(screen: pygame.Surface, rect: pygame.Rect, theme: Theme) -> None:
    unit = max(1, min(rect.width, rect.height) // 8)
    pole_x = rect.centerx
    pygame.draw.line(
        screen,
        theme.mine,
        (pole_x, rect.top + unit * 2),
        (pole_x, rect.bottom - unit * 2),
        max(1, unit // 2),
    )
    pygame.draw.polygon(
        screen,
        theme.flag,
        (
            (pole_x, rect.top + unit * 2),
            (pole_x - unit * 3, rect.top + unit * 3),
            (pole_x, rect.top + unit * 4),
        ),
    )
    pygame.draw.line(
        screen,
        theme.mine,
        (pole_x - unit * 2, rect.bottom - unit * 2),
        (pole_x + unit * 2, rect.bottom - unit * 2),
        max(1, unit // 2),
    )


def _draw_mine(screen: pygame.Surface, rect: pygame.Rect, theme: Theme) -> None:
    radius = max(3, min(rect.width, rect.height) // 4)
    center = rect.center
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        pygame.draw.line(
            screen,
            theme.mine,
            center,
            (center[0] + dx * radius * 2, center[1] + dy * radius * 2),
            max(1, radius // 4),
        )
    pygame.draw.circle(screen, theme.mine, center, radius)
    pygame.draw.circle(
        screen,
        theme.hidden_highlight,
        (center[0] - radius // 3, center[1] - radius // 3),
        max(1, radius // 5),
    )


def _draw_board(screen: pygame.Surface, state: GameState, layout: Layout, theme: Theme) -> None:
    border = layout.board.inflate(6, 6)
    pygame.draw.rect(screen, theme.board_border, border, border_radius=7)
    for row in range(state.height):
        for column in range(state.width):
            position = (row, column)
            cell = state.board[row][column]
            rect = _cell_rect(layout, position)
            show_mine = state.status == "lost" and cell.has_mine
            incorrect_flag = (
                state.status == "lost" and cell.visibility == "flagged" and not cell.has_mine
            )
            if position == state.exploded_cell:
                pygame.draw.rect(screen, theme.danger, rect)
            elif cell.visibility == "revealed" or show_mine:
                pygame.draw.rect(screen, theme.revealed_cell, rect)
            else:
                pygame.draw.rect(screen, theme.hidden_cell, rect)
                pygame.draw.line(screen, theme.hidden_highlight, rect.topleft, rect.topright, 2)
                pygame.draw.line(screen, theme.hidden_highlight, rect.topleft, rect.bottomleft, 2)
            pygame.draw.rect(screen, theme.grid, rect, width=1)

            if show_mine:
                _draw_mine(screen, rect, theme)
            elif cell.visibility == "flagged":
                _draw_flag(screen, rect, theme)
            elif cell.visibility == "revealed" and cell.adjacent_mines:
                number = _font(max(12, int(layout.cell_size * 0.58)), "en", True).render(
                    str(cell.adjacent_mines), True, NUMBER_COLORS[cell.adjacent_mines]
                )
                screen.blit(number, number.get_rect(center=rect.center))
            if incorrect_flag:
                inset = max(3, layout.cell_size // 5)
                pygame.draw.line(
                    screen,
                    theme.danger,
                    (rect.left + inset, rect.top + inset),
                    (rect.right - inset, rect.bottom - inset),
                    max(2, layout.cell_size // 10),
                )
                pygame.draw.line(
                    screen,
                    theme.danger,
                    (rect.right - inset, rect.top + inset),
                    (rect.left + inset, rect.bottom - inset),
                    max(2, layout.cell_size // 10),
                )


def _draw_result_overlay(
    screen: pygame.Surface,
    layout: Layout,
    title: str,
    subtitle: str,
    theme: Theme,
    language: Language,
) -> None:
    panel = pygame.Rect(0, 0, min(330, layout.board.width - 24), 92)
    panel.center = layout.board.center
    shadow = panel.inflate(8, 8)
    surface = pygame.Surface(shadow.size, pygame.SRCALPHA)
    surface.fill((*theme.overlay, 190))
    screen.blit(surface, shadow)
    title_surface = _font(27, language, True).render(title, True, (255, 255, 255))
    subtitle_surface = _font(15, language).render(subtitle, True, (236, 240, 245))
    screen.blit(title_surface, title_surface.get_rect(center=(panel.centerx, panel.centery - 15)))
    screen.blit(
        subtitle_surface,
        subtitle_surface.get_rect(center=(panel.centerx, panel.centery + 22)),
    )


def _draw_settings(
    screen: pygame.Surface,
    theme_name: str,
    language: Language,
    difficulty: Difficulty,
) -> None:
    theme = THEMES[theme_name]
    controls = settings_controls(screen.get_size())
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((*theme.overlay, 165))
    screen.blit(shade, (0, 0))
    pygame.draw.rect(screen, theme.panel, controls.modal, border_radius=18)
    pygame.draw.rect(screen, theme.grid, controls.modal, width=2, border_radius=18)

    title = _font(27, language, True).render(text(language, "settings_title"), True, theme.text)
    screen.blit(title, (controls.modal.left + 28, controls.modal.top + 20))
    _draw_button(screen, controls.close, text(language, "close"), theme, language)

    sections = (
        (text(language, "difficulty"), controls.modal.top + 72),
        (text(language, "theme"), controls.modal.top + 192),
        (text(language, "language"), controls.modal.top + 312),
    )
    for label, y in sections:
        rendered = _font(17, language, True).render(label, True, theme.muted_text)
        screen.blit(rendered, (controls.modal.left + 30, y))
    for name, rect in controls.difficulties.items():
        _draw_button(screen, rect, text(language, name), theme, language, name == difficulty)
    for name, rect in controls.themes.items():
        _draw_button(screen, rect, text(language, name), theme, language, name == theme_name)
    for name, rect in controls.languages.items():
        key = "chinese" if name == "zh" else "english"
        _draw_button(screen, rect, text(language, key), theme, language, name == language)


def _format_time(elapsed_ms: int | None, language: Language) -> str:
    if elapsed_ms is None:
        return text(language, "no_record")
    return f"{min(999, elapsed_ms // 1000):03d}"


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    best_times_ms: dict[Difficulty, int | None],
    theme_name: str,
    language: Language,
    settings_open: bool = False,
) -> Layout:
    """Draw a full Minesweeper frame and return its clickable layout."""

    theme = THEMES[theme_name]
    screen.fill(theme.background)
    layout = page_layout(screen.get_size(), (state.width, state.height))
    title_surface = _font(31, language, True).render(text(language, "title"), True, theme.text)
    screen.blit(title_surface, title_surface.get_rect(midtop=(screen.get_width() // 2, 20)))
    _draw_button(screen, layout.back, text(language, "back"), theme, language)
    _draw_button(
        screen,
        layout.settings,
        text(language, "settings"),
        theme,
        language,
        settings_open,
    )
    _draw_button(screen, layout.restart, text(language, "restart"), theme, language)
    _draw_stat(
        screen,
        layout.mines,
        text(language, "mines"),
        f"{remaining_mines(state):02d}",
        theme,
        language,
    )
    _draw_stat(
        screen,
        layout.timer,
        text(language, "time"),
        _format_time(state.elapsed_ms, language),
        theme,
        language,
    )
    _draw_stat(
        screen,
        layout.best,
        text(language, "best"),
        _format_time(best_times_ms[state.difficulty], language),
        theme,
        language,
    )
    _draw_stat(
        screen,
        layout.difficulty,
        text(language, "difficulty"),
        text(language, state.difficulty),
        theme,
        language,
    )
    _draw_board(screen, state, layout, theme)

    hint_key = "ready" if state.status == "ready" else "hint"
    hint = _font(15, language).render(text(language, hint_key), True, theme.muted_text)
    hint_y = min(screen.get_height() - 22, layout.board.bottom + 23)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, hint_y)))
    if state.status in ("won", "lost"):
        _draw_result_overlay(
            screen,
            layout,
            text(language, state.status),
            text(language, "restart_hint"),
            theme,
            language,
        )
    if settings_open:
        _draw_settings(screen, theme_name, language, state.difficulty)
    return layout
