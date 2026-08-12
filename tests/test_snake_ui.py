"""Tests for responsive Snake layout."""

import unittest

from games.game_snake.ui import mode_controls, page_layout, settings_controls


class SnakeUiTests(unittest.TestCase):
    def test_board_uses_square_cells_and_stays_inside_window(self):
        for window_size in ((560, 520), (820, 700), (1200, 800)):
            with self.subTest(window_size=window_size):
                layout = page_layout(window_size, (24, 18))
                self.assertEqual(layout.board.width, layout.cell_size * 24)
                self.assertEqual(layout.board.height, layout.cell_size * 18)
                self.assertGreaterEqual(layout.board.left, 0)
                self.assertLessEqual(layout.board.right, window_size[0])
                self.assertLessEqual(layout.board.bottom, window_size[1])

    def test_controls_stay_inside_window(self):
        width, height = 560, 520
        layout = page_layout((width, height), (24, 18))
        for control in (
            layout.back,
            layout.settings,
            layout.pause,
            layout.restart,
            layout.score,
            layout.best,
            layout.speed,
            layout.mode,
        ):
            self.assertGreaterEqual(control.left, 0)
            self.assertGreaterEqual(control.top, 0)
            self.assertLessEqual(control.right, width)
            self.assertLessEqual(control.bottom, height)

    def test_settings_controls_stay_inside_modal(self):
        controls = settings_controls((560, 520))
        clickable = [
            controls.close,
            *controls.themes.values(),
            *controls.languages.values(),
            *controls.speeds.values(),
        ]
        self.assertTrue(all(controls.modal.contains(rect) for rect in clickable))

    def test_mode_cards_are_distinct_and_inside_modal(self):
        controls = mode_controls((560, 520))
        self.assertTrue(controls.modal.contains(controls.classic))
        self.assertTrue(controls.modal.contains(controls.wrap))
        self.assertFalse(controls.classic.colliderect(controls.wrap))


if __name__ == "__main__":
    unittest.main()
