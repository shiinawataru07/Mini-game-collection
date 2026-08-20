"""Data-driven game selection menu for the mini-game collection."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from games.common.app_settings import (
    GlobalAction,
    apply_global_action,
    audio_status,
    handle_global_shortcut,
    load_app_settings,
    save_app_settings,
)
from games.common.app_settings_ui import app_settings_controls, draw_app_settings
from games.common.controls import draw_button
from games.common.fonts import get_font
from games.common.window import open_resizable_window, resize_resizable_window, set_fullscreen
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
    settings: pygame.Rect


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
    card_height = max(80, min(330, available_height // rows))
    grid_height = card_height * rows + gap * (rows - 1)
    top = content_top + max(0, (content_bottom - content_top - grid_height) // 2)

    cards: dict[str, pygame.Rect] = {}
    for index, game in enumerate(games):
        row = index // columns
        column = index % columns
        games_in_row = min(columns, count - row * columns)
        row_width = card_width * games_in_row + gap * (games_in_row - 1)
        row_left = (width - row_width) // 2
        cards[game.id] = pygame.Rect(
            row_left + column * (card_width + gap),
            top + row * (card_height + gap),
            card_width,
            card_height,
        )
    settings = pygame.Rect(width - margin - 106, 22, 106, 36)
    return MenuLayout(cards, settings)


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
    compact_without_preview = rect.height < 120
    if not compact_without_preview:
        game.preview(screen, rect)
    title_size = max(22, min(31, rect.height // 6))
    subtitle_size = max(13, min(16, rect.height // 12))
    if compact_without_preview:
        title_y = rect.centery - 13
        subtitle_y = rect.centery + 18
    else:
        title_y = rect.bottom - max(35, min(75, round(rect.height * 0.28)))
        subtitle_y = rect.bottom - max(11, min(40, round(rect.height * 0.15)))
    title_surface = get_font(title_size, "zh", bold=True).render(game.title, True, TEXT)
    subtitle_surface = get_font(subtitle_size, "zh").render(game.subtitle, True, MUTED)
    shortcut_surface = get_font(14, bold=True).render(str(game.shortcut), True, game.accent)
    screen.blit(
        title_surface,
        title_surface.get_rect(center=(rect.centerx, title_y)),
    )
    screen.blit(
        subtitle_surface,
        subtitle_surface.get_rect(center=(rect.centerx, subtitle_y)),
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
    app_settings = load_app_settings()
    screen = open_resizable_window(
        WINDOW_SIZE,
        "Mini Game Collection",
        app_settings.fullscreen,
    )
    clock = pygame.time.Clock()
    settings_open = False

    def apply_setting_action(action: GlobalAction) -> None:
        nonlocal app_settings, screen
        app_settings = apply_global_action(app_settings, action)
        save_app_settings(app_settings)
        if action == "fullscreen":
            screen = set_fullscreen(app_settings.fullscreen, MIN_WINDOW_SIZE)

    while True:
        layout = menu_layout(screen.get_size())
        mouse = pygame.mouse.get_pos()
        screen.fill(BACKGROUND)

        title = get_font(39, "zh", bold=True).render("小游戏合集", True, TEXT)
        subtitle = get_font(17, "zh").render("选择一个游戏开始 · Choose a game", True, MUTED)
        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 58)))
        screen.blit(subtitle, subtitle.get_rect(center=(screen.get_width() // 2, 100)))
        draw_button(
            screen,
            layout.settings,
            "全局设置",
            PANEL,
            TEXT,
            15,
            "zh",
            border_color=BORDER,
            border_radius=9,
        )

        for game in GAMES:
            card = layout.cards[game.id]
            _draw_card(screen, card, game, card.collidepoint(mouse))

        shortcuts = " / ".join(str(game.shortcut) for game in GAMES)
        hint = get_font(13, "zh").render(
            f"按 {shortcuts} 快速选择  ·  {audio_status(app_settings)}  ·  M 静音  ·  F11 全屏",
            True,
            MUTED,
        )
        screen.blit(
            hint,
            hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 27)),
        )
        if settings_open:
            draw_app_settings(screen, app_settings)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.VIDEORESIZE:
                screen = resize_resizable_window((event.w, event.h), MIN_WINDOW_SIZE)
            elif event.type == pygame.KEYDOWN:
                handled = handle_global_shortcut(event.key, app_settings, MIN_WINDOW_SIZE)
                if handled is not None:
                    app_settings, screen = handled
                    continue
                if event.key == pygame.K_F10:
                    settings_open = not settings_open
                elif event.key == pygame.K_ESCAPE and settings_open:
                    settings_open = False
                elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return None
                elif not settings_open:
                    shortcut = _shortcut_from_key(event.key)
                    if shortcut is not None:
                        return game_by_shortcut(shortcut)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if settings_open:
                    controls = app_settings_controls(screen.get_size())
                    if controls.close.collidepoint(event.pos):
                        settings_open = False
                    elif controls.volume_down.collidepoint(event.pos):
                        apply_setting_action("volume_down")
                    elif controls.volume_up.collidepoint(event.pos):
                        apply_setting_action("volume_up")
                    elif controls.mute.collidepoint(event.pos):
                        apply_setting_action("mute")
                    elif controls.fullscreen.collidepoint(event.pos):
                        apply_setting_action("fullscreen")
                elif layout.settings.collidepoint(event.pos):
                    settings_open = True
                else:
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
