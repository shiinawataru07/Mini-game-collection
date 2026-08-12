"""Low-level drawing helpers shared by game-specific controls."""

from __future__ import annotations

import pygame

from .fonts import get_font

Color = tuple[int, int, int]


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
