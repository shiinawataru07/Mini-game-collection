"""Low-level drawing helpers shared by game-specific controls."""

from __future__ import annotations

import pygame

from .fonts import get_font
from .types import Color


def draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    background: Color,
    foreground: Color,
    font_size: int,
    language: str = "en",
    border_color: Color | None = None,
    border_width: int = 1,
    border_radius: int = 8,
    minimum_font_size: int = 14,
) -> None:
    """Draw a rounded text button without imposing game-specific theme rules."""

    pygame.draw.rect(screen, background, rect, border_radius=border_radius)
    if border_color is not None:
        pygame.draw.rect(
            screen,
            border_color,
            rect,
            width=border_width,
            border_radius=border_radius,
        )
    rendered = get_font(
        font_size,
        language,
        bold=True,
        minimum_size=minimum_font_size,
    ).render(label, True, foreground)
    screen.blit(rendered, rendered.get_rect(center=rect.center))


def draw_panel(
    screen: pygame.Surface,
    rect: pygame.Rect,
    background: Color,
    *,
    border_color: Color | None = None,
    border_width: int = 1,
    border_radius: int = 10,
) -> None:
    """Draw a reusable rounded panel with an optional border."""

    pygame.draw.rect(screen, background, rect, border_radius=border_radius)
    if border_color is not None:
        pygame.draw.rect(
            screen,
            border_color,
            rect,
            width=border_width,
            border_radius=border_radius,
        )


def draw_overlay(
    screen: pygame.Surface,
    color: Color,
    alpha: int,
    rect: pygame.Rect | None = None,
) -> None:
    """Cover a screen region with a translucent color."""

    target = rect or screen.get_rect()
    overlay = pygame.Surface(target.size, pygame.SRCALPHA)
    overlay.fill((*color, max(0, min(255, alpha))))
    screen.blit(overlay, target)
