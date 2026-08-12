import unittest

import pygame
from games.game_tetris.config import DEFAULT_LANGUAGE, DEFAULT_THEME, TEXTS, THEMES
from games.game_tetris.logic import new_game
from games.game_tetris.ui import draw_game, page_layout, settings_controls


class TetrisUiTests(unittest.TestCase):
    def test_themes_and_languages_are_available(self):
        self.assertEqual(DEFAULT_THEME, "midnight")
        self.assertEqual(DEFAULT_LANGUAGE, "zh")
        self.assertEqual(set(THEMES), {"midnight", "light", "classic"})
        self.assertEqual(set(TEXTS), {"en", "zh"})

    def test_layout_stays_inside_supported_windows(self):
        for window_size in ((560, 640), (760, 780), (1100, 850)):
            with self.subTest(window_size=window_size):
                bounds_width, bounds_height = window_size
                layout = page_layout(window_size)
                for rect in (
                    layout.board,
                    layout.hold,
                    layout.next,
                    layout.stats,
                    layout.back,
                    layout.pause,
                    layout.restart,
                    layout.settings,
                ):
                    self.assertGreaterEqual(rect.left, 0)
                    self.assertGreaterEqual(rect.top, 0)
                    self.assertLessEqual(rect.right, bounds_width)
                    self.assertLessEqual(rect.bottom, bounds_height)

    def test_settings_controls_stay_inside_modal(self):
        controls = settings_controls((560, 640))
        for rect in (
            controls.close,
            *controls.themes.values(),
            *controls.languages.values(),
        ):
            self.assertTrue(controls.modal.contains(rect))

    def test_game_and_settings_render_at_minimum_size(self):
        pygame.font.init()
        screen = pygame.Surface((560, 640))
        state = new_game()
        layout = draw_game(
            screen,
            state,
            best_score=1200,
            theme_name="midnight",
            language="zh",
            settings_open=True,
        )
        self.assertEqual(layout.board.size, (260, 520))


if __name__ == "__main__":
    unittest.main()
