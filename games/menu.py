"""Game selection menu for the mini-game collection."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Literal

import pygame

Choice = Literal["2048", "snake", "quit"]

WINDOW_SIZE = (760, 600)
MIN_WINDOW_SIZE = (600, 480)
BACKGROUND = (242, 244, 239)
PANEL = (255, 255, 252)
TEXT = (50, 61, 53)
MUTED = (106, 119, 108)
BORDER = (215, 222, 213)


@dataclass(frozen=True)
class MenuLayout:
    game_2048: pygame.Rect
    snake: pygame.Rect


@cache
def _font(size: int, bold: bool = False) -> pygame.font.Font:
    font_path = None
    for name in ("microsoftyahei", "simhei", "simsun", "notosanscjksc"):
        font_path = pygame.font.match_font(name)
        if font_path:
            break
    font = (
        pygame.font.Font(font_path, max(14, size))
        if font_path
        else pygame.font.Font(None, max(14, size))
    )
    font.set_bold(bold)
    return font


def menu_layout(window_size: tuple[int, int]) -> MenuLayout:
    width, height = window_size
    margin = max(22, min(48, width // 15))
    gap = max(18, min(30, width // 24))
    card_width = (width - margin * 2 - gap) // 2
    card_height = max(230, min(330, height - 210))
    top = max(142, (height - card_height) // 2 + 30)
    return MenuLayout(
        pygame.Rect(margin, top, card_width, card_height),
        pygame.Rect(margin + card_width + gap, top, card_width, card_height),
    )


def _draw_2048_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    size = min(128, rect.width - 60, rect.height // 2)
    board = pygame.Rect(0, 0, size, size)
    board.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (187, 173, 160), board, border_radius=9)
    gap = 5
    cell = (size - gap * 5) // 4
    values = ((2, 0, 4, 0), (0, 8, 0, 0), (0, 0, 16, 0), (0, 0, 0, 32))
    colors = {
        0: (205, 193, 180),
        2: (238, 228, 218),
        4: (237, 224, 200),
        8: (242, 177, 121),
        16: (245, 149, 99),
        32: (246, 124, 95),
    }
    for row in range(4):
        for column in range(4):
            cell_rect = pygame.Rect(
                board.left + gap + column * (cell + gap),
                board.top + gap + row * (cell + gap),
                cell,
                cell,
            )
            value = values[row][column]
            pygame.draw.rect(screen, colors[value], cell_rect, border_radius=4)
            if value:
                label = _font(max(14, cell // 2), True).render(str(value), True, (119, 110, 101))
                screen.blit(label, label.get_rect(center=cell_rect.center))


def _draw_snake_preview(screen: pygame.Surface, rect: pygame.Rect) -> None:
    preview = pygame.Rect(0, 0, min(170, rect.width - 50), min(128, rect.height // 2))
    preview.center = (rect.centerx, rect.top + rect.height // 3)
    pygame.draw.rect(screen, (210, 226, 194), preview, border_radius=10)
    cell = max(14, min(preview.width // 9, preview.height // 6))
    cells = ((2, 3), (3, 3), (4, 3), (5, 3), (5, 2), (6, 2))
    origin_x = preview.centerx - cell * 4
    origin_y = preview.centery - cell * 3
    for index, (column, row) in enumerate(cells):
        segment = pygame.Rect(
            origin_x + column * cell + 1, origin_y + row * cell + 1, cell - 2, cell - 2
        )
        pygame.draw.rect(
            screen,
            (63, 125, 68) if index == len(cells) - 1 else (91, 151, 83),
            segment,
            border_radius=cell // 3,
        )
    food_center = (origin_x + 7 * cell + cell // 2, origin_y + 2 * cell + cell // 2)
    pygame.draw.circle(screen, (218, 73, 65), food_center, max(4, cell // 3))


def _draw_card(
    screen: pygame.Surface,
    rect: pygame.Rect,
    title: str,
    subtitle: str,
    accent: tuple[int, int, int],
    hovered: bool,
    preview,
) -> None:
    shadow = rect.move(0, 5)
    pygame.draw.rect(screen, (220, 224, 217), shadow, border_radius=18)
    pygame.draw.rect(screen, PANEL, rect, border_radius=18)
    pygame.draw.rect(
        screen, accent if hovered else BORDER, rect, width=3 if hovered else 1, border_radius=18
    )
    preview(screen, rect)
    title_surface = _font(31, True).render(title, True, TEXT)
    subtitle_surface = _font(16).render(subtitle, True, MUTED)
    screen.blit(title_surface, title_surface.get_rect(center=(rect.centerx, rect.bottom - 75)))
    screen.blit(
        subtitle_surface, subtitle_surface.get_rect(center=(rect.centerx, rect.bottom - 40))
    )


def _choose_game() -> Choice:
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("Mini Game Collection")
    clock = pygame.time.Clock()

    while True:
        layout = menu_layout(screen.get_size())
        mouse = pygame.mouse.get_pos()
        screen.fill(BACKGROUND)

        title = _font(39, True).render("小游戏合集", True, TEXT)
        subtitle = _font(17).render("选择一个游戏开始  ·  Choose a game", True, MUTED)
        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 58)))
        screen.blit(subtitle, subtitle.get_rect(center=(screen.get_width() // 2, 100)))

        _draw_card(
            screen,
            layout.game_2048,
            "2048",
            "数字合并 · 策略",
            (238, 177, 76),
            layout.game_2048.collidepoint(mouse),
            _draw_2048_preview,
        )
        _draw_card(
            screen,
            layout.snake,
            "贪吃蛇",
            "移动成长 · 反应",
            (79, 151, 81),
            layout.snake.collidepoint(mouse),
            _draw_snake_preview,
        )

        hint = _font(14).render("按 1 / 2 快速选择  ·  Esc 退出", True, MUTED)
        screen.blit(hint, hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 27)))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(
                    (max(MIN_WINDOW_SIZE[0], event.w), max(MIN_WINDOW_SIZE[1], event.h)),
                    pygame.RESIZABLE,
                )
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return "quit"
                if event.key in (pygame.K_1, pygame.K_KP1):
                    return "2048"
                if event.key in (pygame.K_2, pygame.K_KP2):
                    return "snake"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if layout.game_2048.collidepoint(event.pos):
                    return "2048"
                if layout.snake.collidepoint(event.pos):
                    return "snake"
        clock.tick(60)


def run() -> None:
    """Show the menu again whenever a game returns to the collection."""

    while True:
        choice = _choose_game()
        if choice == "quit":
            return
        if choice == "2048":
            from games.game_2048.game import run as run_game
        else:
            from games.game_snake.game import run as run_game
        if run_game() == "quit":
            return
