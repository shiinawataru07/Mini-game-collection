import unittest
from dataclasses import replace

import pygame
from games.game_aircraft.logic import Enemy, Explosion, new_game
from games.game_aircraft.ui import BOSS_PATTERN, craft_controls, draw_game, page_layout


class AircraftUiTests(unittest.TestCase):
    def test_layout_stays_inside_supported_windows(self):
        for window_size in ((600, 620), (780, 720), (1200, 900)):
            with self.subTest(window_size=window_size):
                layout = page_layout(window_size)
                bounds = pygame.Rect((0, 0), window_size)
                for rect in (
                    layout.arena,
                    layout.stats,
                    layout.back,
                    layout.pause,
                    layout.restart,
                ):
                    self.assertTrue(bounds.contains(rect))
                self.assertFalse(layout.arena.colliderect(layout.stats))

    def test_ready_game_renders_at_minimum_size(self):
        pygame.font.init()
        screen = pygame.Surface((600, 620))
        layout = draw_game(screen, new_game(), best_score=900)
        self.assertGreaterEqual(layout.arena.height, 500)
        self.assertNotEqual(screen.get_at(layout.arena.center), pygame.Color(0, 0, 0, 255))

    def test_aircraft_selection_cards_stay_inside_modal(self):
        controls = craft_controls((600, 620))
        self.assertEqual(set(controls.cards), {"falcon", "viper", "guardian"})
        for card in controls.cards.values():
            self.assertTrue(controls.modal.contains(card))

    def test_selection_boss_and_explosion_render(self):
        pygame.font.init()
        screen = pygame.Surface((780, 720))
        state = replace(
            new_game("guardian"),
            enemies=(Enemy(1, "boss", 180, 92, 0, 0, 25, 500, max_hp=50),),
            explosions=(Explosion(180, 200, "boss", age_ms=400, duration_ms=1300),),
        )
        draw_game(screen, state, best_score=4000, selecting_craft=True)
        self.assertNotEqual(screen.get_at(screen.get_rect().center), pygame.Color(0, 0, 0, 255))

    def test_boss_sprite_rows_have_equal_width(self):
        self.assertEqual(len({len(row) for row in BOSS_PATTERN}), 1)


if __name__ == "__main__":
    unittest.main()
