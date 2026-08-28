"""Tests for responsive Snake layout."""

import unittest

import pygame
from games.game_snake.logic import new_game
from games.game_snake.maps import BUILTIN_MAPS, new_editor
from games.game_snake.ui import (
    _font_language_for_text,
    _scaled_font_size,
    draw_game,
    draw_map_editor,
    editor_cell_at,
    editor_controls,
    map_library_controls,
    mode_controls,
    page_layout,
    settings_controls,
)


class SnakeUiTests(unittest.TestCase):
    def test_chinese_label_uses_cjk_font_in_english_interface(self):
        self.assertEqual(_font_language_for_text("中文", "en"), "zh")
        self.assertEqual(_font_language_for_text("English", "en"), "en")

    def test_only_english_font_size_is_increased(self):
        self.assertGreater(_scaled_font_size(18, "en"), 18)
        self.assertEqual(_scaled_font_size(18, "zh"), 18)

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
        self.assertTrue(controls.modal.contains(controls.maze))
        self.assertTrue(controls.modal.contains(controls.workshop))
        self.assertFalse(controls.classic.colliderect(controls.wrap))
        self.assertFalse(controls.wrap.colliderect(controls.maze))
        self.assertFalse(controls.maze.colliderect(controls.workshop))

    def test_map_library_controls_fit_at_minimum_size(self):
        controls = map_library_controls((560, 520), 6)
        for rect in (
            *controls.cards,
            controls.editor,
            controls.refresh,
            controls.back,
            controls.previous,
            controls.next,
        ):
            self.assertTrue(controls.modal.contains(rect))

    def test_editor_cell_mapping_and_controls(self):
        controls = editor_controls((560, 520), (24, 18))
        self.assertEqual(editor_cell_at(controls.board.topleft, controls, new_editor()), (0, 0))
        self.assertIsNone(editor_cell_at((0, 0), controls, new_editor()))
        bounds = pygame.Rect(0, 0, 560, 520)
        for rect in (
            controls.board,
            controls.back,
            controls.name,
            controls.clear,
            controls.export,
            controls.play,
        ):
            self.assertTrue(bounds.contains(rect))

    def test_map_library_and_editor_render_at_minimum_size(self):
        pygame.font.init()
        screen = pygame.Surface((560, 520))
        draw_game(
            screen,
            new_game(),
            0,
            "garden",
            "zh",
            "normal",
            map_selecting=True,
            available_maps=BUILTIN_MAPS,
        )
        draw_map_editor(screen, new_editor(), "night", "zh")
        self.assertNotEqual(screen.get_at(screen.get_rect().center), pygame.Color(0, 0, 0, 255))


if __name__ == "__main__":
    unittest.main()
