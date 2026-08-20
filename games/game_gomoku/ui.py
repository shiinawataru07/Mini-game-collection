"""Responsive antique wooden board rendering for Gomoku."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from games.common.controls import draw_button, draw_overlay, draw_panel
from games.common.fonts import get_font

from .config import (
    ACCENT,
    BACKGROUND,
    BLACK_STONE,
    BOARD_SIZE,
    GRID,
    MUTED_TEXT,
    PANEL,
    PANEL_DARK,
    TEXT,
    WHITE_STONE,
    WOOD,
    WOOD_DARK,
    WOOD_LIGHT,
)
from .logic import GameState, Position


@dataclass(frozen=True)
class Layout:
    board: pygame.Rect
    back: pygame.Rect
    mode: pygame.Rect
    undo: pygame.Rect
    restart: pygame.Rect
    spacing: int
    padding: int


@dataclass(frozen=True)
class ModeControls:
    modal: pygame.Rect
    close: pygame.Rect
    local: pygame.Rect
    ai: pygame.Rect


def page_layout(window_size: tuple[int, int]) -> Layout:
    width, height = window_size
    header = 92
    footer = 34
    available = min(width - 28, height - header - footer)
    spacing = max(20, available // 16)
    board_size = spacing * 16
    board = pygame.Rect(0, header, board_size, board_size)
    board.centerx = width // 2
    padding = spacing

    margin = max(14, min(24, width // 30))
    button_width = max(72, min(94, (width - margin * 2 - 30) // 4))
    back = pygame.Rect(margin, 18, button_width, 36)
    mode = pygame.Rect(back.right + 10, back.top, button_width, back.height)
    restart = pygame.Rect(width - margin - button_width, back.top, button_width, back.height)
    undo = pygame.Rect(restart.left - 10 - button_width, back.top, button_width, back.height)
    return Layout(board, back, mode, undo, restart, spacing, padding)


def mode_controls(window_size: tuple[int, int]) -> ModeControls:
    width, height = window_size
    modal = pygame.Rect(0, 0, min(620, width - 36), min(350, height - 36))
    modal.center = (width // 2, height // 2)
    close = pygame.Rect(modal.right - 88, modal.top + 18, 66, 34)
    gap = 18
    card_width = (modal.width - 72 - gap) // 2
    local = pygame.Rect(modal.left + 36, modal.top + 108, card_width, 170)
    ai = pygame.Rect(local.right + gap, local.top, card_width, local.height)
    return ModeControls(modal, close, local, ai)


def _intersection(layout: Layout, position: Position) -> tuple[int, int]:
    row, column = position
    origin_x = layout.board.left + layout.padding
    origin_y = layout.board.top + layout.padding
    return origin_x + column * layout.spacing, origin_y + row * layout.spacing


def position_at_point(layout: Layout, point: tuple[int, int]) -> Position | None:
    if not layout.board.collidepoint(point):
        return None
    origin_x = layout.board.left + layout.padding
    origin_y = layout.board.top + layout.padding
    column = round((point[0] - origin_x) / layout.spacing)
    row = round((point[1] - origin_y) / layout.spacing)
    if not (0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE):
        return None
    center = _intersection(layout, (row, column))
    tolerance = layout.spacing * 0.46
    if abs(point[0] - center[0]) > tolerance or abs(point[1] - center[1]) > tolerance:
        return None
    return row, column


def _draw_wood(screen: pygame.Surface, layout: Layout) -> None:
    board = layout.board
    pygame.draw.rect(screen, WOOD_DARK, board, border_radius=10)
    inner = board.inflate(-8, -8)
    pygame.draw.rect(screen, WOOD, inner, border_radius=7)
    for offset in range(12, inner.height, 13):
        y = inner.top + offset
        points = []
        for x in range(inner.left + 4, inner.right - 3, 10):
            wave = round(math.sin((x + offset * 3) * 0.035) * 2)
            points.append((x, y + wave))
        if len(points) > 1:
            color = WOOD_LIGHT if offset % 26 else WOOD_DARK
            pygame.draw.lines(screen, color, False, points, 1)

    start_x = board.left + layout.padding
    start_y = board.top + layout.padding
    end_x = start_x + layout.spacing * (BOARD_SIZE - 1)
    end_y = start_y + layout.spacing * (BOARD_SIZE - 1)
    for index in range(BOARD_SIZE):
        coordinate_x = start_x + index * layout.spacing
        coordinate_y = start_y + index * layout.spacing
        pygame.draw.line(screen, GRID, (start_x, coordinate_y), (end_x, coordinate_y), 1)
        pygame.draw.line(screen, GRID, (coordinate_x, start_y), (coordinate_x, end_y), 1)

    radius = max(3, layout.spacing // 9)
    for position in ((3, 3), (3, 11), (7, 7), (11, 3), (11, 11)):
        pygame.draw.circle(screen, GRID, _intersection(layout, position), radius)


def _draw_stone(
    screen: pygame.Surface,
    center: tuple[int, int],
    player: int,
    radius: int,
    highlighted: bool = False,
) -> None:
    pygame.draw.circle(screen, (75, 48, 28), (center[0] + 2, center[1] + 3), radius)
    if player == 1:
        pygame.draw.circle(screen, BLACK_STONE, center, radius)
        pygame.draw.circle(
            screen,
            (82, 82, 78),
            (center[0] - radius // 3, center[1] - radius // 3),
            max(2, radius // 5),
        )
    else:
        pygame.draw.circle(screen, (160, 151, 132), center, radius)
        pygame.draw.circle(screen, WHITE_STONE, center, max(2, radius - 1))
        pygame.draw.circle(
            screen,
            (255, 253, 242),
            (center[0] - radius // 3, center[1] - radius // 3),
            max(2, radius // 4),
        )
    if highlighted:
        pygame.draw.circle(screen, ACCENT, center, max(2, radius // 5), width=2)


def _draw_board(screen: pygame.Surface, state: GameState, layout: Layout) -> None:
    _draw_wood(screen, layout)
    if state.winning_line:
        start = _intersection(layout, state.winning_line[0])
        end = _intersection(layout, state.winning_line[-1])
        pygame.draw.line(screen, ACCENT, start, end, max(3, layout.spacing // 8))

    radius = max(8, round(layout.spacing * 0.43))
    last = state.moves[-1] if state.moves else None
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            player = state.board[row][column]
            if player:
                position = (row, column)
                _draw_stone(
                    screen,
                    _intersection(layout, position),
                    player,
                    radius,
                    position == last,
                )

    if state.status == "playing" and pygame.display.get_init():
        hover = position_at_point(layout, pygame.mouse.get_pos())
        if hover is not None and state.board[hover[0]][hover[1]] == 0:
            ghost = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            color = (*BLACK_STONE, 90) if state.current_player == 1 else (*WHITE_STONE, 145)
            pygame.draw.circle(ghost, color, (radius + 2, radius + 2), radius)
            center = _intersection(layout, hover)
            screen.blit(ghost, (center[0] - radius - 2, center[1] - radius - 2))


def _status_text(state: GameState) -> str:
    if state.status == "black_won":
        return "黑方胜利"
    if state.status == "white_won":
        return "白方胜利"
    if state.status == "draw":
        return "和棋"
    return "黑方落子" if state.current_player == 1 else "白方落子"


def _draw_mode_selection(
    screen: pygame.Surface,
    notice: str,
    closable: bool,
) -> None:
    controls = mode_controls(screen.get_size())
    draw_overlay(screen, (34, 25, 18), 180)
    draw_panel(
        screen,
        controls.modal,
        PANEL,
        border_color=WOOD_DARK,
        border_width=2,
        border_radius=18,
    )
    title = get_font(29, "zh", bold=True).render("选择对局模式", True, TEXT)
    screen.blit(title, title.get_rect(center=(controls.modal.centerx, controls.modal.top + 48)))
    if closable:
        draw_button(
            screen,
            controls.close,
            "关闭",
            PANEL_DARK,
            TEXT,
            15,
            "zh",
            border_color=WOOD_DARK,
        )

    pygame.draw.rect(screen, WOOD_LIGHT, controls.local, border_radius=14)
    pygame.draw.rect(screen, WOOD_DARK, controls.local, width=2, border_radius=14)
    local_title = get_font(24, "zh", bold=True).render("本地双人", True, TEXT)
    local_subtitle = get_font(15, "zh").render("黑白双方轮流落子", True, MUTED_TEXT)
    local_key = get_font(14, bold=True).render("1", True, ACCENT)
    screen.blit(
        local_title, local_title.get_rect(center=(controls.local.centerx, controls.local.top + 55))
    )
    screen.blit(
        local_subtitle,
        local_subtitle.get_rect(center=(controls.local.centerx, controls.local.top + 96)),
    )
    screen.blit(
        local_key, local_key.get_rect(center=(controls.local.centerx, controls.local.bottom - 28))
    )

    pygame.draw.rect(screen, (213, 201, 176), controls.ai, border_radius=14)
    pygame.draw.rect(screen, (170, 151, 119), controls.ai, width=1, border_radius=14)
    ai_title = get_font(24, "zh", bold=True).render("人机对战", True, MUTED_TEXT)
    ai_subtitle = get_font(15, "zh").render("AI 开发中 · 后续开放", True, MUTED_TEXT)
    screen.blit(ai_title, ai_title.get_rect(center=(controls.ai.centerx, controls.ai.top + 55)))
    screen.blit(
        ai_subtitle,
        ai_subtitle.get_rect(center=(controls.ai.centerx, controls.ai.top + 96)),
    )
    if notice:
        rendered = get_font(14, "zh").render(notice, True, ACCENT)
        screen.blit(
            rendered, rendered.get_rect(center=(controls.modal.centerx, controls.modal.bottom - 25))
        )


def draw_game(
    screen: pygame.Surface,
    state: GameState,
    mode_selecting: bool = False,
    mode_notice: str = "",
    mode_closable: bool = False,
) -> Layout:
    layout = page_layout(screen.get_size())
    screen.fill(BACKGROUND)
    for rect, label in (
        (layout.back, "返回"),
        (layout.mode, "模式"),
        (layout.undo, "悔棋"),
        (layout.restart, "重开"),
    ):
        draw_button(
            screen,
            rect,
            label,
            PANEL,
            TEXT,
            16,
            "zh",
            border_color=WOOD_DARK,
            border_radius=9,
        )
    status = get_font(21, "zh", bold=True).render(_status_text(state), True, PANEL)
    move_count = get_font(14, "zh").render(f"第 {len(state.moves) + 1} 手", True, PANEL_DARK)
    screen.blit(status, status.get_rect(center=(screen.get_width() // 2, 66)))
    if state.status == "playing":
        screen.blit(
            move_count,
            move_count.get_rect(
                midleft=(status.get_rect(center=(screen.get_width() // 2, 66)).right + 12, 66)
            ),
        )

    _draw_board(screen, state, layout)
    hint = get_font(13, "zh").render(
        "点击交叉点落子 · U 悔棋 · R 重开 · M 静音 · F11 全屏",
        True,
        PANEL_DARK,
    )
    screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 18)))

    if state.status != "playing" and not mode_selecting:
        panel = pygame.Rect(0, 0, min(330, layout.board.width - 30), 100)
        panel.center = layout.board.center
        draw_overlay(screen, (48, 31, 19), 135, layout.board)
        draw_panel(screen, panel, PANEL, border_color=WOOD_DARK, border_width=2, border_radius=14)
        title = get_font(30, "zh", bold=True).render(_status_text(state), True, TEXT)
        subtitle = get_font(15, "zh").render("可悔棋继续，或按 R 重新开始", True, MUTED_TEXT)
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.centery - 16)))
        screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.centery + 25)))

    if mode_selecting:
        _draw_mode_selection(screen, mode_notice, mode_closable)
    return layout
