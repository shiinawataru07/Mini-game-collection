"""Responsive Pygame layout and drawing for Snake."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pygame

from .config import (
    DEFAULT_LANGUAGE,
    SPEED_ORDER,
    THEMES,
    Language,
    Speed,
    Theme,
    moves_per_second,
    text,
)
from .logic import Direction, GameMode, GameState


@dataclass(frozen=True)
class Layout:
    board: pygame.Rect
    back: pygame.Rect
    pause: pygame.Rect
    restart: pygame.Rect
    settings: pygame.Rect
    score: pygame.Rect
    best: pygame.Rect
    speed: pygame.Rect
    mode: pygame.Rect
    cell_size: int


@dataclass(frozen=True)
class SettingsControls:
    modal: pygame.Rect
    close: pygame.Rect
    themes: dict[str, pygame.Rect]
    languages: dict[Language, pygame.Rect]
    speeds: dict[Speed, pygame.Rect]


@dataclass(frozen=True)
class ModeControls:
    modal: pygame.Rect
    classic: pygame.Rect
    wrap: pygame.Rect


@lru_cache(maxsize=None)
def _font(size: int, language: Language = DEFAULT_LANGUAGE, bold: bool = False) -> pygame.font.Font:
    size = max(14, size)
    font_path = None
    if language == "zh":
        for name in ("microsoftyahei", "simhei", "simsun", "notosanscjksc"):
            font_path = pygame.font.match_font(name)
            if font_path:
                break
    font = pygame.font.Font(font_path, size) if font_path else pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


def page_layout(window_size: tuple[int, int], grid_size: tuple[int, int]) -> Layout:
    """Calculate a centered integer-cell board and all interactive controls."""

    width, height = window_size
    columns, rows = grid_size
    margin = max(12, min(24, min(width, height) // 24))
    header_height = max(124, min(152, height // 4))
    footer_height = 52
    available_width = max(columns, width - margin * 2)
    available_height = max(rows, height - header_height - footer_height)
    cell_size = max(1, min(available_width // columns, available_height // rows))
    board_width = cell_size * columns
    board_height = cell_size * rows
    board = pygame.Rect((width - board_width) // 2, header_height, board_width, board_height)

    button_width = max(72, min(96, width // 8))
    button_height = 36
    back = pygame.Rect(margin, 20, button_width, button_height)
    settings = pygame.Rect(back.right + 8, 20, button_width, button_height)
    restart = pygame.Rect(width - margin - button_width, 20, button_width, button_height)
    pause = pygame.Rect(restart.left - 10 - button_width, 20, button_width, button_height)

    card_width = max(72, min(104, (width - margin * 2 - 24) // 4))
    card_gap = 8
    cards_width = card_width * 4 + card_gap * 3
    cards_left = (width - cards_width) // 2
    card_y = 70
    score = pygame.Rect(cards_left, card_y, card_width, 48)
    best = pygame.Rect(score.right + card_gap, card_y, card_width, 48)
    speed = pygame.Rect(best.right + card_gap, card_y, card_width, 48)
    mode = pygame.Rect(speed.right + card_gap, card_y, card_width, 48)
    return Layout(board, back, pause, restart, settings, score, best, speed, mode, cell_size)


def settings_controls(window_size: tuple[int, int]) -> SettingsControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(480, width - 36), min(410, height - 36))
    modal.center = (width // 2, height // 2)
    close = pygame.Rect(modal.right - 92, modal.top + 18, 70, 34)
    content_left = modal.left + 30
    content_width = modal.width - 60
    gap = 10

    theme_width = (content_width - gap * 2) // 3
    themes = {
        name: pygame.Rect(content_left + index * (theme_width + gap), modal.top + 105, theme_width, 45)
        for index, name in enumerate(THEMES)
    }
    language_width = (content_width - gap) // 2
    languages: dict[Language, pygame.Rect] = {
        "zh": pygame.Rect(content_left, modal.top + 205, language_width, 45),
        "en": pygame.Rect(content_left + language_width + gap, modal.top + 205, language_width, 45),
    }
    speed_width = (content_width - gap * 2) // 3
    speeds = {
        name: pygame.Rect(content_left + index * (speed_width + gap), modal.top + 305, speed_width, 45)
        for index, name in enumerate(SPEED_ORDER)
    }
    return SettingsControls(modal, close, themes, languages, speeds)


def mode_controls(window_size: tuple[int, int]) -> ModeControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(520, width - 36), min(330, height - 36))
    modal.center = (width // 2, height // 2)
    gap = 18
    card_width = (modal.width - 54 - gap) // 2
    classic = pygame.Rect(modal.left + 27, modal.top + 105, card_width, 155)
    wrap = pygame.Rect(classic.right + gap, classic.top, card_width, 155)
    return ModeControls(modal, classic, wrap)


def _draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    theme: Theme,
    language: Language,
    active: bool = False,
    enabled: bool = True,
) -> None:
    color = theme.accent if active else theme.panel
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, theme.grid, rect, width=1, border_radius=10)
    text_color = theme.panel if active else (theme.text if enabled else theme.muted_text)
    surface = _font(18, language, True).render(label, True, text_color)
    screen.blit(surface, surface.get_rect(center=rect.center))


def _draw_stat(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    value: str,
    theme: Theme,
    language: Language,
) -> None:
    pygame.draw.rect(screen, theme.panel, rect, border_radius=10)
    label_surface = _font(13, language).render(label, True, theme.muted_text)
    value_surface = _font(20, language, True).render(value, True, theme.text)
    screen.blit(label_surface, label_surface.get_rect(midtop=(rect.centerx, rect.top + 4)))
    screen.blit(value_surface, value_surface.get_rect(midbottom=(rect.centerx, rect.bottom - 4)))


def _cell_rect(layout: Layout, cell: tuple[int, int], padding: int = 2) -> pygame.Rect:
    column, row = cell
    return pygame.Rect(
        layout.board.left + column * layout.cell_size + padding,
        layout.board.top + row * layout.cell_size + padding,
        max(1, layout.cell_size - padding * 2),
        max(1, layout.cell_size - padding * 2),
    )


def _draw_board(screen: pygame.Surface, state: GameState, layout: Layout, theme: Theme) -> None:
    pygame.draw.rect(screen, theme.board, layout.board, border_radius=9)
    for column in range(1, state.width):
        x = layout.board.left + column * layout.cell_size
        pygame.draw.line(screen, theme.grid, (x, layout.board.top), (x, layout.board.bottom))
    for row in range(1, state.height):
        y = layout.board.top + row * layout.cell_size
        pygame.draw.line(screen, theme.grid, (layout.board.left, y), (layout.board.right, y))

    if state.food is not None:
        food_rect = _cell_rect(layout, state.food, max(2, layout.cell_size // 7))
        center = food_rect.center
        radius = max(3, min(food_rect.width, food_rect.height) // 2)
        pygame.draw.circle(screen, theme.food, center, radius)
        leaf_rect = pygame.Rect(center[0] + radius // 5, center[1] - radius, radius, max(2, radius // 2))
        pygame.draw.ellipse(screen, theme.food_detail, leaf_rect)

    for index in range(len(state.snake) - 1, -1, -1):
        cell = state.snake[index]
        rect = _cell_rect(layout, cell, max(1, layout.cell_size // 12))
        color = theme.snake_head if index == 0 else theme.snake_body
        pygame.draw.rect(screen, color, rect, border_radius=max(3, layout.cell_size // 4))

    _draw_eyes(screen, state, layout, theme)


def _draw_eyes(screen: pygame.Surface, state: GameState, layout: Layout, theme: Theme) -> None:
    head = _cell_rect(layout, state.snake[0], max(1, layout.cell_size // 12))
    radius = max(1, layout.cell_size // 11)
    offset = max(2, layout.cell_size // 5)
    cx, cy = head.center
    positions: dict[Direction, tuple[tuple[int, int], tuple[int, int]]] = {
        "right": ((cx + offset, cy - offset), (cx + offset, cy + offset)),
        "left": ((cx - offset, cy - offset), (cx - offset, cy + offset)),
        "up": ((cx - offset, cy - offset), (cx + offset, cy - offset)),
        "down": ((cx - offset, cy + offset), (cx + offset, cy + offset)),
    }
    for position in positions[state.direction]:
        pygame.draw.circle(screen, theme.snake_detail, position, radius + 1)
        pygame.draw.circle(screen, theme.text, position, radius)


def _draw_overlay(
    screen: pygame.Surface,
    layout: Layout,
    title: str,
    subtitle: str,
    theme: Theme,
    language: Language,
) -> None:
    overlay = pygame.Surface(layout.board.size, pygame.SRCALPHA)
    overlay.fill((*theme.overlay, 180))
    screen.blit(overlay, layout.board)
    title_surface = _font(max(28, layout.cell_size * 2), language, True).render(title, True, (255, 255, 255))
    subtitle_surface = _font(max(16, layout.cell_size), language).render(subtitle, True, (238, 242, 236))
    center_x, center_y = layout.board.center
    screen.blit(title_surface, title_surface.get_rect(center=(center_x, center_y - 18)))
    screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(center_x, center_y + 30)))


def _draw_settings(
    screen: pygame.Surface,
    theme_name: str,
    language: Language,
    speed: Speed,
) -> None:
    theme = THEMES[theme_name]
    controls = settings_controls(screen.get_size())
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((*theme.overlay, 150))
    screen.blit(shade, (0, 0))
    pygame.draw.rect(screen, theme.panel, controls.modal, border_radius=18)
    pygame.draw.rect(screen, theme.grid, controls.modal, width=2, border_radius=18)

    title = _font(27, language, True).render(text(language, "settings_title"), True, theme.text)
    screen.blit(title, (controls.modal.left + 28, controls.modal.top + 20))
    _draw_button(screen, controls.close, text(language, "close"), theme, language)

    sections = (
        (text(language, "theme"), controls.modal.top + 76),
        (text(language, "language"), controls.modal.top + 176),
        (text(language, "speed"), controls.modal.top + 276),
    )
    for label, y in sections:
        surface = _font(17, language, True).render(label, True, theme.muted_text)
        screen.blit(surface, (controls.modal.left + 30, y))

    for name, rect in controls.themes.items():
        _draw_button(screen, rect, text(language, name), theme, language, name == theme_name)
    for name, rect in controls.languages.items():
        key = "chinese" if name == "zh" else "english"
        _draw_button(screen, rect, text(language, key), theme, language, name == language)
    for name, rect in controls.speeds.items():
        _draw_button(screen, rect, text(language, name), theme, language, name == speed)


def _draw_mode_selection(
    screen: pygame.Surface,
    theme_name: str,
    language: Language,
) -> None:
    theme = THEMES[theme_name]
    controls = mode_controls(screen.get_size())
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((*theme.overlay, 175))
    screen.blit(shade, (0, 0))
    pygame.draw.rect(screen, theme.panel, controls.modal, border_radius=20)
    pygame.draw.rect(screen, theme.grid, controls.modal, width=2, border_radius=20)

    title = _font(29, language, True).render(text(language, "choose_mode"), True, theme.text)
    screen.blit(title, title.get_rect(center=(controls.modal.centerx, controls.modal.top + 48)))
    for mode, rect in (("classic", controls.classic), ("wrap", controls.wrap)):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, theme.background, rect, border_radius=14)
        pygame.draw.rect(screen, theme.accent if hovered else theme.grid, rect, width=3 if hovered else 1, border_radius=14)
        mode_title = _font(23, language, True).render(text(language, mode), True, theme.text)
        shortcut = _font(18, language, True).render("1" if mode == "classic" else "2", True, theme.accent)
        screen.blit(shortcut, shortcut.get_rect(center=(rect.centerx, rect.top + 30)))
        screen.blit(mode_title, mode_title.get_rect(center=(rect.centerx, rect.top + 72)))
        description_font = _font(14, language)
        words = text(language, f"{mode}_desc").split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if current and description_font.size(candidate)[0] > rect.width - 18:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        for index, line in enumerate(lines[:2]):
            description = description_font.render(line, True, theme.muted_text)
            screen.blit(description, description.get_rect(center=(rect.centerx, rect.top + 108 + index * 20)))


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    best_score: int,
    theme_name: str,
    language: Language,
    speed: Speed,
    settings_open: bool = False,
    mode_selecting: bool = False,
) -> Layout:
    """Draw one complete frame and return the current clickable layout."""

    theme = THEMES[theme_name]
    screen.fill(theme.background)
    layout = page_layout(screen.get_size(), (state.width, state.height))

    title_surface = _font(30, language, True).render(text(language, "title"), True, theme.text)
    screen.blit(title_surface, title_surface.get_rect(midtop=(screen.get_width() // 2, 22)))

    _draw_button(screen, layout.back, text(language, "back"), theme, language)
    _draw_button(
        screen,
        layout.settings,
        text(language, "settings"),
        theme,
        language,
        settings_open,
        state.status == "paused",
    )
    pause_label = text(language, "continue" if state.status == "paused" else "pause")
    _draw_button(screen, layout.pause, pause_label, theme, language, state.status == "paused")
    _draw_button(screen, layout.restart, text(language, "restart"), theme, language)
    _draw_stat(screen, layout.score, text(language, "score"), str(state.score), theme, language)
    _draw_stat(screen, layout.best, text(language, "best"), str(best_score), theme, language)
    _draw_stat(
        screen,
        layout.speed,
        text(language, "speed"),
        f"{text(language, speed)} · {moves_per_second(speed):.0f}",
        theme,
        language,
    )
    _draw_stat(
        screen,
        layout.mode,
        text(language, "mode"),
        text(language, f"{state.mode}_short"),
        theme,
        language,
    )

    _draw_board(screen, state, layout, theme)

    hint = _font(15, language).render(text(language, "hint"), True, theme.muted_text)
    hint_y = min(screen.get_height() - 24, layout.board.bottom + 22)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, hint_y)))

    if state.status == "ready" and not mode_selecting:
        _draw_overlay(screen, layout, text(language, "ready"), "WASD / ↑ ↓ ← →", theme, language)
    elif state.status == "paused" and not settings_open:
        _draw_overlay(screen, layout, text(language, "paused"), text(language, "continue"), theme, language)
    elif state.status in ("game_over", "won"):
        key = "won" if state.status == "won" else "game_over"
        _draw_overlay(screen, layout, text(language, key), text(language, "restart_hint"), theme, language)
    if settings_open:
        _draw_settings(screen, theme_name, language, speed)
    elif mode_selecting:
        _draw_mode_selection(screen, theme_name, language)
    return layout
