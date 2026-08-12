"""Data-driven game selection menu for the mini-game collection."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from games.common.fonts import get_font
from games.common.window import open_resizable_window, resize_resizable_window
from games.registry import GAMES, GameDescriptor, game_by_shortcut

WINDOW_SIZE = (760, 600)
MIN_WINDOW_SIZE = (600, 480)
BACKGROUND = (242, 244, 239)
PANEL = (255, 255, 252)
TEXT = (50, 61, 53)
MUTED = (106, 119, 108)
BORDER = (215, 222, 213)


@dataclass(frozen=True)
class MenuLayout:
    cards: dict[str, pygame.Rect]


def menu_layout(
    window_size: tuple[int, int],
    games: tuple[GameDescriptor, ...] = GAMES,
) -> MenuLayout:
    """Arrange registered games in a centered grid of up to three columns."""

    width, height = window_size
    count = max(1, len(games))
    columns = min(3, count)
    rows = math.ceil(count / columns)
    margin = max(22, min(48, width // 15))
    gap = max(14, min(26, width // 26))
    available_width = width - margin * 2 - gap * (columns - 1)
    card_width = min(320, available_width // columns)
    content_top = 132
    content_bottom = height - 54
    available_height = content_bottom - content_top - gap * (rows - 1)
    card_height = max(120, min(330, available_height // rows))
    grid_width = card_width * columns + gap * (columns - 1)
    grid_height = card_height * rows + gap * (rows - 1)
    left = (width - grid_width) // 2
    top = content_top + max(0, (content_bottom - content_top - grid_height) // 2)

    cards = {
        game.id: pygame.Rect(
            left + (index % columns) * (card_width + gap),
            top + (index // columns) * (card_height + gap),
            card_width,
            card_height,
        )
        for index, game in enumerate(games)
    }
    return MenuLayout(cards)


def _draw_card(
    screen: pygame.Surface,
    rect: pygame.Rect,
    game: GameDescriptor,
    hovered: bool,
) -> None:
    shadow = rect.move(0, 5)
    pygame.draw.rect(screen, (220, 224, 217), shadow, border_radius=18)
    pygame.draw.rect(screen, PANEL, rect, border_radius=18)
    pygame.draw.rect(
        screen,
        game.accent if hovered else BORDER,
        rect,
        width=3 if hovered else 1,
        border_radius=18,
    )
    game.preview(screen, rect)
    title_surface = get_font(31, "zh", bold=True).render(game.title, True, TEXT)
    subtitle_surface = get_font(16, "zh").render(game.subtitle, True, MUTED)
    shortcut_surface = get_font(14, bold=True).render(str(game.shortcut), True, game.accent)
    screen.blit(title_surface, title_surface.get_rect(center=(rect.centerx, rect.bottom - 75)))
    screen.blit(
        subtitle_surface,
        subtitle_surface.get_rect(center=(rect.centerx, rect.bottom - 40)),
    )
    screen.blit(shortcut_surface, (rect.left + 14, rect.top + 12))


def _shortcut_from_key(key: int) -> int | None:
    for game in GAMES:
        if key in (
            getattr(pygame, f"K_{game.shortcut}", None),
            getattr(pygame, f"K_KP{game.shortcut}", None),
        ):
            return game.shortcut
    return None


def _choose_game() -> GameDescriptor | None:
    screen = open_resizable_window(WINDOW_SIZE, "Mini Game Collection")
    clock = pygame.time.Clock()

    while True:
        layout = menu_layout(screen.get_size())
        mouse = pygame.mouse.get_pos()
        screen.fill(BACKGROUND)

        title = get_font(39, "zh", bold=True).render("小游戏合集", True, TEXT)
        subtitle = get_font(17, "zh").render("选择一个游戏开始 · Choose a game", True, MUTED)
        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 58)))
        screen.blit(subtitle, subtitle.get_rect(center=(screen.get_width() // 2, 100)))

        for game in GAMES:
            card = layout.cards[game.id]
            _draw_card(screen, card, game, card.collidepoint(mouse))

        shortcuts = " / ".join(str(game.shortcut) for game in GAMES)
        hint = get_font(14, "zh").render(f"按 {shortcuts} 快速选择  ·  Esc 退出", True, MUTED)
        screen.blit(
            hint,
            hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 27)),
        )
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.VIDEORESIZE:
                screen = resize_resizable_window((event.w, event.h), MIN_WINDOW_SIZE)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return None
                shortcut = _shortcut_from_key(event.key)
                if shortcut is not None:
                    return game_by_shortcut(shortcut)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for game in GAMES:
                    if layout.cards[game.id].collidepoint(event.pos):
                        return game
        clock.tick(60)


def run() -> None:
    """Show the menu again whenever a registered game returns to the collection."""

    while True:
        game = _choose_game()
        if game is None:
            return
        if game.load_runner()() == "quit":
            return
