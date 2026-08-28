"""Responsive Pygame layout and drawing for Snake."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import pygame

from games.common.controls import draw_button, draw_overlay, draw_panel
from games.common.fonts import get_font

from .config import (
    BONUS_FOOD_DURATION_MS,
    DEFAULT_LANGUAGE,
    SPEED_ORDER,
    THEMES,
    Language,
    Speed,
    Theme,
    moves_per_second,
    text,
)
from .logic import Direction, GameState
from .maps import BUILTIN_MAPS, EditorState, SnakeMap, protected_cells

ENGLISH_FONT_SCALE = 1.15


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
    maze: pygame.Rect
    workshop: pygame.Rect


@dataclass(frozen=True)
class MapLibraryControls:
    modal: pygame.Rect
    cards: tuple[pygame.Rect, ...]
    editor: pygame.Rect
    refresh: pygame.Rect
    back: pygame.Rect
    previous: pygame.Rect
    next: pygame.Rect


@dataclass(frozen=True)
class EditorControls:
    board: pygame.Rect
    back: pygame.Rect
    name: pygame.Rect
    clear: pygame.Rect
    export: pygame.Rect
    play: pygame.Rect
    cell_size: int


def _scaled_font_size(size: int, language: Language) -> int:
    """Compensate for the default Latin font's smaller visual size."""

    return round(size * ENGLISH_FONT_SCALE) if language == "en" else size


def _font_language_for_text(label: str, language: Language) -> Language:
    """Use a CJK-capable font whenever a label contains Chinese characters."""

    if any("\u3400" <= character <= "\u9fff" for character in label):
        return "zh"
    return language


def _font(size: int, language: Language = DEFAULT_LANGUAGE, bold: bool = False) -> pygame.font.Font:
    return get_font(_scaled_font_size(size, language), language, bold, minimum_size=14)


def _mouse_position() -> tuple[int, int]:
    return pygame.mouse.get_pos() if pygame.display.get_init() else (-1, -1)


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
        name: pygame.Rect(
            content_left + index * (theme_width + gap), modal.top + 105, theme_width, 45
        )
        for index, name in enumerate(THEMES)
    }
    language_width = (content_width - gap) // 2
    languages: dict[Language, pygame.Rect] = {
        "zh": pygame.Rect(content_left, modal.top + 205, language_width, 45),
        "en": pygame.Rect(content_left + language_width + gap, modal.top + 205, language_width, 45),
    }
    speed_width = (content_width - gap * 2) // 3
    speeds = {
        name: pygame.Rect(
            content_left + index * (speed_width + gap), modal.top + 305, speed_width, 45
        )
        for index, name in enumerate(SPEED_ORDER)
    }
    return SettingsControls(modal, close, themes, languages, speeds)


def mode_controls(window_size: tuple[int, int]) -> ModeControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(700, width - 36), min(440, height - 36))
    modal.center = (width // 2, height // 2)
    gap = 12
    card_width = (modal.width - 54 - gap) // 2
    card_height = max(115, (modal.height - 135 - gap) // 2)
    classic = pygame.Rect(modal.left + 27, modal.top + 82, card_width, card_height)
    wrap = pygame.Rect(classic.right + gap, classic.top, card_width, card_height)
    maze = pygame.Rect(classic.left, classic.bottom + gap, card_width, card_height)
    workshop = pygame.Rect(wrap.left, wrap.bottom + gap, card_width, card_height)
    return ModeControls(modal, classic, wrap, maze, workshop)


def map_library_controls(window_size: tuple[int, int], count: int) -> MapLibraryControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(760, width - 28), min(570, height - 28))
    modal.center = (width // 2, height // 2)
    gap = 10
    columns = 3 if modal.width >= 650 else 2
    rows = 2 if columns == 3 else 3
    card_width = (modal.width - 44 - gap * (columns - 1)) // columns
    card_height = max(78, (modal.height - 160 - gap * (rows - 1)) // rows)
    cards = tuple(
        pygame.Rect(
            modal.left + 22 + (index % columns) * (card_width + gap),
            modal.top + 72 + (index // columns) * (card_height + gap),
            card_width,
            card_height,
        )
        for index in range(min(6, count))
    )
    button_width = max(78, min(108, (modal.width - 80) // 5))
    button_y = modal.bottom - 48
    back = pygame.Rect(modal.left + 20, button_y, button_width, 32)
    editor = pygame.Rect(back.right + 8, button_y, button_width, 32)
    refresh = pygame.Rect(editor.right + 8, button_y, button_width, 32)
    next_button = pygame.Rect(modal.right - 20 - button_width, button_y, button_width, 32)
    previous = pygame.Rect(next_button.left - 8 - button_width, button_y, button_width, 32)
    return MapLibraryControls(modal, cards, editor, refresh, back, previous, next_button)


def editor_controls(window_size: tuple[int, int], grid_size: tuple[int, int]) -> EditorControls:
    width, height = window_size
    columns, rows = grid_size
    margin = 16
    header = 126
    footer = 38
    cell_size = max(1, min((width - margin * 2) // columns, (height - header - footer) // rows))
    board = pygame.Rect(0, header, cell_size * columns, cell_size * rows)
    board.centerx = width // 2
    gap = 7
    button_width = max(70, min(94, (width - margin * 2 - gap * 4) // 5))
    controls_width = button_width * 5 + gap * 4
    left = (width - controls_width) // 2
    buttons = [
        pygame.Rect(left + index * (button_width + gap), 18, button_width, 34) for index in range(5)
    ]
    return EditorControls(board, *buttons, cell_size)


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
    text_color = theme.panel if active else (theme.text if enabled else theme.muted_text)
    font_language = _font_language_for_text(label, language)
    draw_button(
        screen,
        rect,
        label,
        color,
        text_color,
        _scaled_font_size(18, font_language),
        font_language,
        border_color=theme.grid,
        border_radius=10,
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

    for cell in state.walls:
        wall_rect = _cell_rect(layout, cell, max(1, layout.cell_size // 14))
        pygame.draw.rect(
            screen, theme.maze_wall, wall_rect, border_radius=max(2, layout.cell_size // 7)
        )
        highlight = wall_rect.inflate(
            -max(3, layout.cell_size // 4), -max(3, layout.cell_size // 4)
        )
        if highlight.width > 0 and highlight.height > 0:
            pygame.draw.rect(screen, theme.grid, highlight, width=1, border_radius=2)

    if state.food is not None:
        food_rect = _cell_rect(layout, state.food, max(2, layout.cell_size // 7))
        center = food_rect.center
        radius = max(3, min(food_rect.width, food_rect.height) // 2)
        pygame.draw.circle(screen, theme.food, center, radius)
        leaf_rect = pygame.Rect(
            center[0] + radius // 5, center[1] - radius, radius, max(2, radius // 2)
        )
        pygame.draw.ellipse(screen, theme.food_detail, leaf_rect)

    if state.bonus_food is not None:
        bonus_rect = _cell_rect(layout, state.bonus_food, max(2, layout.cell_size // 9))
        center = bonus_rect.center
        radius = max(4, min(bonus_rect.width, bonus_rect.height) // 2)
        pygame.draw.circle(screen, theme.bonus_food, center, radius)
        diamond_radius = max(2, radius // 2)
        pygame.draw.polygon(
            screen,
            theme.bonus_detail,
            (
                (center[0], center[1] - diamond_radius),
                (center[0] + diamond_radius, center[1]),
                (center[0], center[1] + diamond_radius),
                (center[0] - diamond_radius, center[1]),
            ),
        )
        timer_fraction = max(0.0, min(1.0, state.bonus_remaining_ms / BONUS_FOOD_DURATION_MS))
        timer_rect = bonus_rect.inflate(5, 5)
        pygame.draw.arc(
            screen,
            theme.bonus_detail,
            timer_rect,
            -math.pi / 2,
            -math.pi / 2 + math.tau * timer_fraction,
            max(2, layout.cell_size // 12),
        )

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
    draw_overlay(screen, theme.overlay, 180, layout.board)
    title_surface = _font(max(28, layout.cell_size * 2), language, True).render(
        title, True, (255, 255, 255)
    )
    subtitle_surface = _font(max(16, layout.cell_size), language).render(
        subtitle, True, (238, 242, 236)
    )
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
    draw_overlay(screen, theme.overlay, 150)
    draw_panel(
        screen,
        controls.modal,
        theme.panel,
        border_color=theme.grid,
        border_width=2,
        border_radius=18,
    )

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
    draw_overlay(screen, theme.overlay, 175)
    draw_panel(
        screen,
        controls.modal,
        theme.panel,
        border_color=theme.grid,
        border_width=2,
        border_radius=20,
    )

    title = _font(29, language, True).render(text(language, "choose_mode"), True, theme.text)
    screen.blit(title, title.get_rect(center=(controls.modal.centerx, controls.modal.top + 48)))
    for mode, rect in (
        ("classic", controls.classic),
        ("wrap", controls.wrap),
        ("maze", controls.maze),
        ("workshop", controls.workshop),
    ):
        hovered = rect.collidepoint(_mouse_position())
        pygame.draw.rect(screen, theme.background, rect, border_radius=14)
        pygame.draw.rect(
            screen,
            theme.accent if hovered else theme.grid,
            rect,
            width=3 if hovered else 1,
            border_radius=14,
        )
        mode_title = _font(23, language, True).render(text(language, mode), True, theme.text)
        shortcut_text = {"classic": "1", "wrap": "2", "maze": "3", "workshop": "4"}[mode]
        shortcut = _font(18, language, True).render(shortcut_text, True, theme.accent)
        screen.blit(shortcut, shortcut.get_rect(center=(rect.centerx, rect.top + 21)))
        screen.blit(mode_title, mode_title.get_rect(center=(rect.centerx, rect.top + 49)))
        description_font = _font(14, language)
        description_text = text(language, f"{mode}_desc")
        separator = " " if " " in description_text else ""
        words = description_text.split(" ") if separator else list(description_text)
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current}{separator}{word}"
            if current and description_font.size(candidate)[0] > rect.width - 18:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        for index, line in enumerate(lines[:2]):
            description = description_font.render(line, True, theme.muted_text)
            screen.blit(
                description,
                description.get_rect(center=(rect.centerx, rect.top + 81 + index * 19)),
            )


def _draw_mini_map(
    screen: pygame.Surface,
    game_map: SnakeMap,
    area: pygame.Rect,
    theme: Theme,
) -> None:
    scale = max(1, min(area.width // game_map.width, area.height // game_map.height))
    board = pygame.Rect(0, 0, scale * game_map.width, scale * game_map.height)
    board.center = area.center
    pygame.draw.rect(screen, theme.board, board, border_radius=4)
    for column, row in game_map.walls:
        pygame.draw.rect(
            screen,
            theme.maze_wall,
            (board.left + column * scale, board.top + row * scale, scale, scale),
        )
    pygame.draw.rect(screen, theme.grid, board, width=1, border_radius=4)


def _draw_map_library(
    screen: pygame.Surface,
    maps: Sequence[SnakeMap],
    page: int,
    theme_name: str,
    language: Language,
    message: str,
) -> None:
    theme = THEMES[theme_name]
    start = page * 6
    visible = maps[start : start + 6]
    controls = map_library_controls(screen.get_size(), len(visible))
    draw_overlay(screen, theme.overlay, 185)
    draw_panel(
        screen,
        controls.modal,
        theme.panel,
        border_color=theme.grid,
        border_width=2,
        border_radius=18,
    )
    title = _font(27, language, True).render(text(language, "choose_map"), True, theme.text)
    screen.blit(title, title.get_rect(center=(controls.modal.centerx, controls.modal.top + 32)))
    page_count = max(1, math.ceil(len(maps) / 6))
    page_surface = _font(13, language).render(f"{page + 1} / {page_count}", True, theme.muted_text)
    screen.blit(page_surface, (controls.modal.right - 65, controls.modal.top + 24))

    for visible_index, (game_map, rect) in enumerate(
        zip(visible, controls.cards, strict=False), start=1
    ):
        hovered = rect.collidepoint(_mouse_position())
        pygame.draw.rect(screen, theme.background, rect, border_radius=10)
        pygame.draw.rect(
            screen,
            theme.accent if hovered else theme.grid,
            rect,
            width=3 if hovered else 1,
            border_radius=10,
        )
        preview = pygame.Rect(
            rect.left + 8, rect.top + 8, rect.width - 16, max(34, rect.height - 54)
        )
        _draw_mini_map(screen, game_map, preview, theme)
        name = _font(15, language, True).render(game_map.name[:18], True, theme.text)
        source_key = "builtin_map" if game_map in BUILTIN_MAPS else "custom_map"
        source = _font(11, language).render(text(language, source_key), True, theme.muted_text)
        shortcut = _font(12, language, True).render(str(visible_index), True, theme.accent)
        screen.blit(shortcut, (rect.left + 7, rect.top + 4))
        screen.blit(name, name.get_rect(midbottom=(rect.centerx, rect.bottom - 20)))
        screen.blit(source, source.get_rect(midbottom=(rect.centerx, rect.bottom - 5)))

    _draw_button(screen, controls.back, text(language, "map_back"), theme, language)
    _draw_button(screen, controls.editor, text(language, "new_map"), theme, language)
    _draw_button(screen, controls.refresh, text(language, "refresh_maps"), theme, language)
    _draw_button(
        screen,
        controls.previous,
        text(language, "previous_page"),
        theme,
        language,
        enabled=page > 0,
    )
    _draw_button(
        screen,
        controls.next,
        text(language, "next_page"),
        theme,
        language,
        enabled=page + 1 < page_count,
    )
    footer = (message or text(language, "drop_map_hint"))[:82]
    footer_surface = _font(12, language).render(footer, True, theme.muted_text)
    screen.blit(
        footer_surface,
        footer_surface.get_rect(center=(controls.modal.centerx, controls.modal.bottom - 66)),
    )


def editor_cell_at(
    position: tuple[int, int],
    controls: EditorControls,
    editor: EditorState,
) -> tuple[int, int] | None:
    if not controls.board.collidepoint(position):
        return None
    return (
        (position[0] - controls.board.left) // controls.cell_size,
        (position[1] - controls.board.top) // controls.cell_size,
    )


def draw_map_editor(
    screen: pygame.Surface,
    editor: EditorState,
    theme_name: str,
    language: Language,
) -> EditorControls:
    theme = THEMES[theme_name]
    controls = editor_controls(screen.get_size(), (editor.width, editor.height))
    screen.fill(theme.background)
    title = _font(23, language, True).render(text(language, "workshop"), True, theme.text)
    screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 72)))
    _draw_button(screen, controls.back, text(language, "map_back"), theme, language)
    _draw_button(
        screen,
        controls.name,
        f"{text(language, 'map_name')}*" if editor.editing_name else text(language, "map_name"),
        theme,
        language,
        editor.editing_name,
    )
    _draw_button(screen, controls.clear, text(language, "clear_map"), theme, language)
    _draw_button(screen, controls.export, text(language, "export_map"), theme, language)
    _draw_button(screen, controls.play, text(language, "play_map"), theme, language)
    name = _font(17, language, True).render((editor.name or "_")[:26], True, theme.accent)
    screen.blit(name, name.get_rect(center=(screen.get_width() // 2, 99)))

    pygame.draw.rect(screen, theme.board, controls.board, border_radius=8)
    for column in range(editor.width + 1):
        x = controls.board.left + column * controls.cell_size
        pygame.draw.line(screen, theme.grid, (x, controls.board.top), (x, controls.board.bottom))
    for row in range(editor.height + 1):
        y = controls.board.top + row * controls.cell_size
        pygame.draw.line(screen, theme.grid, (controls.board.left, y), (controls.board.right, y))
    for cell in protected_cells(editor.width, editor.height):
        rect = pygame.Rect(
            controls.board.left + cell[0] * controls.cell_size + 1,
            controls.board.top + cell[1] * controls.cell_size + 1,
            max(1, controls.cell_size - 1),
            max(1, controls.cell_size - 1),
        )
        pygame.draw.rect(screen, theme.snake_body, rect)
    for column, row in editor.walls:
        rect = pygame.Rect(
            controls.board.left + column * controls.cell_size + 1,
            controls.board.top + row * controls.cell_size + 1,
            max(1, controls.cell_size - 1),
            max(1, controls.cell_size - 1),
        )
        pygame.draw.rect(
            screen, theme.maze_wall, rect, border_radius=max(1, controls.cell_size // 7)
        )
    pygame.draw.rect(screen, theme.accent, controls.board, width=2, border_radius=8)
    hint = _font(12, language).render(text(language, "editor_hint"), True, theme.muted_text)
    message = _font(12, language, True).render(editor.message[:70], True, theme.text)
    bottom = min(screen.get_height() - 8, controls.board.bottom + 19)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, bottom)))
    screen.blit(message, message.get_rect(center=(screen.get_width() // 2, bottom + 17)))
    return controls


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    best_score: int,
    theme_name: str,
    language: Language,
    speed: Speed,
    settings_open: bool = False,
    mode_selecting: bool = False,
    map_selecting: bool = False,
    available_maps: Sequence[SnakeMap] = (),
    map_page: int = 0,
    map_message: str = "",
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
        state.map_name[:10] if state.mode == "custom" else text(language, f"{state.mode}_short"),
        theme,
        language,
    )

    _draw_board(screen, state, layout, theme)

    hint_text = text(language, "hint")
    if state.bonus_food is not None:
        hint_text = f"{text(language, 'bonus_food')} · {state.bonus_remaining_ms / 1000:.1f}s"
    hint = _font(15, language).render(hint_text, True, theme.muted_text)
    hint_y = min(screen.get_height() - 24, layout.board.bottom + 22)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, hint_y)))

    if state.status == "ready" and not mode_selecting and not map_selecting:
        _draw_overlay(screen, layout, text(language, "ready"), "WASD / ↑ ↓ ← →", theme, language)
    elif state.status == "paused" and not settings_open:
        _draw_overlay(
            screen, layout, text(language, "paused"), text(language, "continue"), theme, language
        )
    elif state.status in ("game_over", "won"):
        key = "won" if state.status == "won" else "game_over"
        _draw_overlay(
            screen, layout, text(language, key), text(language, "restart_hint"), theme, language
        )
    if settings_open:
        _draw_settings(screen, theme_name, language, speed)
    elif mode_selecting:
        _draw_mode_selection(screen, theme_name, language)
    elif map_selecting:
        _draw_map_library(
            screen,
            available_maps,
            map_page,
            theme_name,
            language,
            map_message,
        )
    return layout
