"""Tests for responsive Minesweeper layout and hit detection."""

import unittest

from games.game_minesweeper.config import DIFFICULTIES
from games.game_minesweeper.ui import cell_at_position, page_layout, settings_controls


class MinesweeperUiTests(unittest.TestCase):
    def test_all_difficulties_use_square_cells_inside_window(self):
        for window_size in ((640, 520), (900, 700), (1200, 800)):
            for difficulty, spec in DIFFICULTIES.items():
                with self.subTest(window_size=window_size, difficulty=difficulty):
                    layout = page_layout(window_size, (spec.width, spec.height))
                    self.assertEqual(layout.board.width, layout.cell_size * spec.width)
                    self.assertEqual(layout.board.height, layout.cell_size * spec.height)
                    self.assertGreaterEqual(layout.board.left, 0)
                    self.assertGreaterEqual(layout.board.top, 0)
                    self.assertLessEqual(layout.board.right, window_size[0])
                    self.assertLessEqual(layout.board.bottom, window_size[1])

    def test_header_controls_stay_inside_window(self):
        width, height = 640, 520
        layout = page_layout((width, height), (30, 16))
        for control in (
            layout.back,
            layout.settings,
            layout.restart,
            layout.mines,
            layout.timer,
            layout.best,
            layout.difficulty,
        ):
            self.assertGreaterEqual(control.left, 0)
            self.assertGreaterEqual(control.top, 0)
            self.assertLessEqual(control.right, width)
            self.assertLessEqual(control.bottom, height)

    def test_mouse_position_maps_to_row_and_column(self):
        layout = page_layout((900, 700), (9, 9))
        point = (
            layout.board.left + layout.cell_size * 4 + 1,
            layout.board.top + layout.cell_size * 3 + 1,
        )
        self.assertEqual(cell_at_position(layout, point), (3, 4))
        self.assertIsNone(cell_at_position(layout, (layout.board.right, layout.board.bottom)))

    def test_settings_controls_are_distinct_and_inside_modal(self):
        controls = settings_controls((640, 520))
        clickable = [
            controls.close,
            *controls.difficulties.values(),
            *controls.themes.values(),
            *controls.languages.values(),
        ]
        self.assertTrue(all(controls.modal.contains(rect) for rect in clickable))
        difficulty_rects = list(controls.difficulties.values())
        self.assertTrue(
            all(
                not first.colliderect(second)
                for index, first in enumerate(difficulty_rects)
                for second in difficulty_rects[index + 1 :]
            )
        )


if __name__ == "__main__":
    unittest.main()
