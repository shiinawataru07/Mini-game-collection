"""Cached font selection with Chinese fallback support."""

from __future__ import annotations

from functools import cache

import pygame

CJK_FONT_NAMES = ("microsoftyahei", "simhei", "simsun", "notosanscjksc")


@cache
def get_font(
    size: int,
    language: str = "en",
    bold: bool = False,
    minimum_size: int = 14,
) -> pygame.font.Font:
    """Return a cached font, preferring a CJK-capable family for Chinese."""

    font_path = None
    if language == "zh":
        for name in CJK_FONT_NAMES:
            font_path = pygame.font.match_font(name)
            if font_path:
                break
    font_size = max(minimum_size, size)
    font = (
        pygame.font.Font(font_path, font_size) if font_path else pygame.font.Font(None, font_size)
    )
    font.set_bold(bold)
    return font
