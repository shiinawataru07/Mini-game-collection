"""Constants and colors for Pixel Aircraft Battle."""

from __future__ import annotations

from games.common.types import Color

WINDOW_SIZE = (780, 720)
MIN_WINDOW_SIZE = (600, 620)
FPS = 60
FIXED_STEP_MS = 1000.0 / FPS

ARENA_WIDTH = 360
ARENA_HEIGHT = 600

RAPID_FIRE_DURATION_MS = 8000.0
PLAYER_INVULNERABLE_MS = 1500.0

BACKGROUND: Color = (8, 13, 30)
PANEL: Color = (17, 25, 50)
PANEL_LIGHT: Color = (27, 39, 70)
GRID: Color = (37, 55, 88)
TEXT: Color = (226, 240, 255)
MUTED: Color = (125, 151, 184)
CYAN: Color = (55, 226, 213)
YELLOW: Color = (255, 218, 91)
RED: Color = (255, 88, 104)
PURPLE: Color = (173, 110, 255)
GREEN: Color = (103, 235, 142)
