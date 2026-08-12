"""Responsive layout and drawing for Tetris."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from games.common.controls import draw_button, draw_overlay, draw_panel
from games.common.fonts import get_font

from .animation import LineClearAnimation
from .config import HIDDEN_ROWS, THEMES, VISIBLE_HEIGHT, Language, Theme, text
from .logic import GameState, active_cells, ghost_y
from .pieces import PIECE_IDS, PieceKind, cells


@dataclass(frozen=True)
class Layout:
    board: pygame.Rect
    hold: pygame.Rect
    next: pygame.Rect
    stats: pygame.Rect
    back: pygame.Rect
    pause: pygame.Rect
    restart: pygame.Rect
    settings: pygame.Rect
    cell_size: int


@dataclass(frozen=True)
class SettingsControls:
    modal: pygame.Rect
    close: pygame.Rect
    themes: dict[str, pygame.Rect]
    languages: dict[Language, pygame.Rect]


def page_layout(window_size: tuple[int, int]) -> Layout:
    width, height = window_size
    margin = max(12, min(22, width // 30))
    header = 82
    footer = 38
    side_width = max(94, min(128, (width - 330) // 2))
    gap = max(10, min(18, width // 45))
    available_board_width = width - margin * 2 - side_width * 2 - gap * 2
    available_board_height = height - header - footer
    cell_size = max(18, min(available_board_width // 10, available_board_height // 20))
    board = pygame.Rect(0, 0, cell_size * 10, cell_size * VISIBLE_HEIGHT)
    board.centerx = width // 2
    board.top = header

    hold = pygame.Rect(
        board.left - gap - side_width, board.top, side_width, min(142, board.height // 4)
    )
    stats = pygame.Rect(hold.left, hold.bottom + gap, side_width, min(220, board.height // 2))
    next_panel = pygame.Rect(
        board.right + gap,
        board.top,
        side_width,
        min(board.height, max(360, board.height * 3 // 4)),
    )

    button_width = max(72, min(96, (width - margin * 2 - 24) // 4))
    button_height = 34
    back = pygame.Rect(margin, 20, button_width, button_height)
    pause = pygame.Rect(back.right + 8, 20, button_width, button_height)
    restart = pygame.Rect(width - margin - button_width, 20, button_width, button_height)
    settings = pygame.Rect(restart.left - 8 - button_width, 20, button_width, button_height)
    return Layout(board, hold, next_panel, stats, back, pause, restart, settings, cell_size)


def settings_controls(window_size: tuple[int, int]) -> SettingsControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(500, width - 36), min(390, height - 36))
    modal.center = (width // 2, height // 2)
    close = pygame.Rect(modal.right - 92, modal.top + 18, 70, 34)
    left = modal.left + 30
    content_width = modal.width - 60
    gap = 10
    theme_width = (content_width - gap * 2) // 3
    themes = {
        name: pygame.Rect(left + index * (theme_width + gap), modal.top + 115, theme_width, 46)
        for index, name in enumerate(THEMES)
    }
    language_width = (content_width - gap) // 2
    languages: dict[Language, pygame.Rect] = {
        "zh": pygame.Rect(left, modal.top + 245, language_width, 46),
        "en": pygame.Rect(left + language_width + gap, modal.top + 245, language_width, 46),
    }
    return SettingsControls(modal, close, themes, languages)


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
        16,
        language,
        border_color=theme.grid,
        border_radius=9,
    )


def _draw_block(
    screen: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    ghost: bool = False,
) -> None:
    if ghost:
        pygame.draw.rect(screen, color, rect, width=max(1, rect.width // 9), border_radius=3)
        return
    pygame.draw.rect(screen, color, rect, border_radius=max(2, rect.width // 8))
    highlight = tuple(min(255, channel + 42) for channel in color)
    pygame.draw.line(
        screen,
        highlight,
        (rect.left + 3, rect.top + 2),
        (rect.right - 4, rect.top + 2),
        max(1, rect.width // 12),
    )


def _board_cell(layout: Layout, column: int, visible_row: int, padding: int = 1) -> pygame.Rect:
    return pygame.Rect(
        layout.board.left + column * layout.cell_size + padding,
        layout.board.top + visible_row * layout.cell_size + padding,
        layout.cell_size - padding * 2,
        layout.cell_size - padding * 2,
    )


def _draw_board(
    screen: pygame.Surface,
    state: GameState,
    layout: Layout,
    theme: Theme,
    animation: LineClearAnimation | None,
    now: int,
) -> None:
    pygame.draw.rect(screen, theme.board, layout.board, border_radius=6)
    for row in range(VISIBLE_HEIGHT):
        for column in range(10):
            board_row = row + HIDDEN_ROWS
            value = state.board[board_row][column]
            rect = _board_cell(layout, column, row)
            if value:
                _draw_block(screen, rect, theme.pieces[value])
            else:
                pygame.draw.rect(screen, theme.grid, rect, width=1, border_radius=2)

    ghost_row = ghost_y(state)
    if state.status != "game_over" and ghost_row != state.active.y:
        for column, row in cells(
            state.active.kind,
            state.active.rotation,
            state.active.x,
            ghost_row,
        ):
            if row >= HIDDEN_ROWS:
                _draw_block(
                    screen,
                    _board_cell(layout, column, row - HIDDEN_ROWS, 3),
                    theme.ghost,
                    ghost=True,
                )

    if state.status != "game_over":
        color = theme.pieces[PIECE_IDS[state.active.kind]]
        for column, row in active_cells(state):
            if row >= HIDDEN_ROWS:
                _draw_block(screen, _board_cell(layout, column, row - HIDDEN_ROWS), color)

    if animation is not None:
        alpha = round(190 * (1.0 - animation.progress(now)))
        flash = pygame.Surface((layout.board.width, layout.cell_size), pygame.SRCALPHA)
        flash.fill((*theme.text, alpha))
        for board_row in animation.rows:
            visible_row = board_row - HIDDEN_ROWS
            if 0 <= visible_row < VISIBLE_HEIGHT:
                screen.blit(
                    flash, (layout.board.left, layout.board.top + visible_row * layout.cell_size)
                )

    pygame.draw.rect(screen, theme.accent, layout.board, width=2, border_radius=6)


def _draw_mini_piece(
    screen: pygame.Surface,
    kind: PieceKind,
    area: pygame.Rect,
    theme: Theme,
    scale: int,
) -> None:
    shape = cells(kind, 0)
    min_x = min(column for column, _ in shape)
    max_x = max(column for column, _ in shape)
    min_y = min(row for _, row in shape)
    max_y = max(row for _, row in shape)
    width = (max_x - min_x + 1) * scale
    height = (max_y - min_y + 1) * scale
    origin_x = area.centerx - width // 2 - min_x * scale
    origin_y = area.centery - height // 2 - min_y * scale
    color = theme.pieces[PIECE_IDS[kind]]
    for column, row in shape:
        rect = pygame.Rect(
            origin_x + column * scale + 1, origin_y + row * scale + 1, scale - 2, scale - 2
        )
        _draw_block(screen, rect, color)


def _draw_side_panels(
    screen: pygame.Surface,
    state: GameState,
    best_score: int,
    layout: Layout,
    theme: Theme,
    language: Language,
) -> None:
    font = get_font(15, language, bold=True)
    small = get_font(13, language)
    draw_panel(screen, layout.hold, theme.panel, border_color=theme.grid, border_radius=11)
    title = font.render(text(language, "hold"), True, theme.muted_text)
    screen.blit(title, title.get_rect(midtop=(layout.hold.centerx, layout.hold.top + 9)))
    if state.hold is not None:
        area = layout.hold.inflate(-8, -32).move(0, 12)
        _draw_mini_piece(screen, state.hold, area, theme, max(12, min(22, area.width // 5)))

    draw_panel(screen, layout.next, theme.panel, border_color=theme.grid, border_radius=11)
    title = font.render(text(language, "next"), True, theme.muted_text)
    screen.blit(title, title.get_rect(midtop=(layout.next.centerx, layout.next.top + 9)))
    slot_height = max(52, (layout.next.height - 38) // 5)
    for index, kind in enumerate(state.next_queue[:5]):
        area = pygame.Rect(
            layout.next.left + 5,
            layout.next.top + 32 + index * slot_height,
            layout.next.width - 10,
            slot_height,
        )
        _draw_mini_piece(
            screen, kind, area, theme, max(10, min(18, area.width // 6, slot_height // 3))
        )

    draw_panel(screen, layout.stats, theme.panel, border_color=theme.grid, border_radius=11)
    stats = (
        (text(language, "score"), state.score),
        (text(language, "best"), max(best_score, state.score)),
        (text(language, "lines"), state.lines),
        (text(language, "level"), state.level),
    )
    row_height = layout.stats.height // len(stats)
    for index, (label, value) in enumerate(stats):
        center_y = layout.stats.top + index * row_height + row_height // 2
        label_surface = small.render(label, True, theme.muted_text)
        value_surface = get_font(19, bold=True).render(str(value), True, theme.text)
        screen.blit(
            label_surface, label_surface.get_rect(midbottom=(layout.stats.centerx, center_y - 1))
        )
        screen.blit(
            value_surface, value_surface.get_rect(midtop=(layout.stats.centerx, center_y + 1))
        )


def _draw_settings(
    screen: pygame.Surface,
    theme_name: str,
    language: Language,
) -> None:
    theme = THEMES[theme_name]
    draw_overlay(screen, (0, 0, 0), 150)
    controls = settings_controls(screen.get_size())
    draw_panel(screen, controls.modal, theme.panel, border_color=theme.grid, border_radius=11)
    heading = get_font(28, language, bold=True).render(text(language, "settings"), True, theme.text)
    screen.blit(heading, (controls.modal.left + 28, controls.modal.top + 22))
    _button(screen, controls.close, text(language, "close"), theme, language)

    label = get_font(17, language, bold=True).render(
        text(language, "theme"), True, theme.muted_text
    )
    screen.blit(label, (controls.modal.left + 30, controls.modal.top + 82))
    for name, rect in controls.themes.items():
        _button(screen, rect, text(language, name), theme, language, name == theme_name)

    label = get_font(17, language, bold=True).render(
        text(language, "language"), True, theme.muted_text
    )
    screen.blit(label, (controls.modal.left + 30, controls.modal.top + 212))
    for selected, rect in controls.languages.items():
        key = "chinese" if selected == "zh" else "english"
        _button(screen, rect, text(language, key), theme, language, selected == language)


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    best_score: int,
    theme_name: str,
    language: Language,
    settings_open: bool = False,
    animation: LineClearAnimation | None = None,
    now: int = 0,
) -> Layout:
    theme = THEMES[theme_name]
    layout = page_layout(screen.get_size())
    screen.fill(theme.background)
    _button(screen, layout.back, text(language, "back"), theme, language)
    pause_key = "resume" if state.status == "paused" else "pause"
    _button(screen, layout.pause, text(language, pause_key), theme, language)
    _button(screen, layout.restart, text(language, "restart"), theme, language)
    _button(screen, layout.settings, text(language, "settings"), theme, language)
    _draw_board(screen, state, layout, theme, animation, now)
    _draw_side_panels(screen, state, best_score, layout, theme, language)

    hint = get_font(13, language).render(text(language, "hint"), True, theme.muted_text)
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 19)))

    if state.status in ("paused", "game_over") and not settings_open:
        draw_overlay(screen, (0, 0, 0), 175, layout.board)
        key = "paused" if state.status == "paused" else "game_over"
        label = get_font(35, language, bold=True).render(text(language, key), True, theme.text)
        screen.blit(label, label.get_rect(center=layout.board.center))
        if state.status == "game_over":
            sub = get_font(16, language).render(
                text(language, "restart_hint"), True, theme.muted_text
            )
            screen.blit(sub, sub.get_rect(center=(layout.board.centerx, layout.board.centery + 43)))

    if settings_open:
        _draw_settings(screen, theme_name, language)
    return layout
