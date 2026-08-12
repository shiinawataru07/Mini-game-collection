import unittest

import pygame
from games.common.controls import draw_overlay, draw_panel


class CommonControlTests(unittest.TestCase):
    def test_panel_draws_fill_and_border(self):
        screen = pygame.Surface((40, 40))
        screen.fill((0, 0, 0))
        rect = pygame.Rect(5, 5, 30, 30)
        draw_panel(
            screen,
            rect,
            (20, 30, 40),
            border_color=(200, 210, 220),
            border_width=2,
            border_radius=0,
        )
        self.assertEqual(screen.get_at((20, 20))[:3], (20, 30, 40))
        self.assertEqual(screen.get_at((5, 20))[:3], (200, 210, 220))

    def test_overlay_can_cover_only_one_region(self):
        screen = pygame.Surface((40, 40))
        screen.fill((255, 255, 255))
        draw_overlay(screen, (0, 0, 0), 255, pygame.Rect(10, 10, 20, 20))
        self.assertEqual(screen.get_at((0, 0))[:3], (255, 255, 255))
        self.assertEqual(screen.get_at((20, 20))[:3], (0, 0, 0))

    def test_overlay_alpha_is_clamped(self):
        screen = pygame.Surface((10, 10))
        screen.fill((255, 255, 255))
        draw_overlay(screen, (0, 0, 0), 999)
        self.assertEqual(screen.get_at((5, 5))[:3], (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
