"""Tests for responsive Minesweeper layout and hit detection."""

import unittest

import pygame
from games.game_minesweeper.config import DIFFICULTIES
from games.game_minesweeper.logic import new_custom_game, new_game
from games.game_minesweeper.solver import Hint
from games.game_minesweeper.ui import (
    _format_mine_count,
    cell_at_position,
    draw_game,
    page_layout,
    settings_controls,
)


class MinesweeperUiTests(unittest.TestCase):
    def test_remaining_mines_can_be_displayed_as_negative(self):
        self.assertEqual(_format_mine_count(8), "08")
        self.assertEqual(_format_mine_count(-2), "-2")

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
            layout.hint,
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
            *controls.custom_decrease.values(),
            *controls.custom_increase.values(),
            *controls.custom_values.values(),
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

    def test_custom_board_and_settings_render_at_minimum_window_size(self):
        pygame.font.init()
        screen = pygame.Surface((640, 520))
        best_times = {"beginner": None, "intermediate": None, "expert": None}
        state = new_custom_game(30, 20, 120)
        layout = draw_game(
            screen,
            state,
            best_times,
            "classic",
            "zh",
            settings_open=True,
        )
        self.assertLessEqual(layout.board.right, 640)
        self.assertLessEqual(layout.board.bottom, 520)

    def test_game_draws_with_an_active_solver_hint(self):
        pygame.font.init()
        screen = pygame.Surface((900, 700))
        best_times = {"beginner": None, "intermediate": None, "expert": None}
        layout = draw_game(
            screen,
            new_game(),
            best_times,
            "classic",
            "zh",
            active_hint=Hint((4, 4), "safe"),
            hint_message_key="hint_safe",
        )
        self.assertTrue(layout.board.collidepoint(layout.board.center))


if __name__ == "__main__":
    unittest.main()
