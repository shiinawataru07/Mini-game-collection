import unittest

import pygame
from games.game_gomoku.logic import new_game, place_stone
from games.game_gomoku.ui import (
    draw_game,
    mode_controls,
    page_layout,
    position_at_point,
)


class GomokuUiTests(unittest.TestCase):
    def test_layout_stays_inside_supported_windows(self):
        for window_size in ((620, 600), (760, 820), (1100, 850)):
            with self.subTest(window_size=window_size):
                width, height = window_size
                layout = page_layout(window_size)
                for rect in (
                    layout.board,
                    layout.back,
                    layout.mode,
                    layout.undo,
                    layout.restart,
                ):
                    self.assertGreaterEqual(rect.left, 0)
                    self.assertGreaterEqual(rect.top, 0)
                    self.assertLessEqual(rect.right, width)
                    self.assertLessEqual(rect.bottom, height)

    def test_mode_controls_are_contained_in_modal(self):
        for window_size in ((620, 600), (760, 820)):
            controls = mode_controls(window_size)
            for rect in (
                controls.close,
                controls.local,
                controls.ai,
                controls.easy,
                controls.normal,
                controls.expert,
            ):
                self.assertTrue(controls.modal.contains(rect))
            self.assertFalse(controls.local.colliderect(controls.ai))
            self.assertTrue(controls.ai.contains(controls.easy))
            self.assertTrue(controls.ai.contains(controls.normal))
            self.assertTrue(controls.ai.contains(controls.expert))

    def test_click_maps_to_intersection_and_rejects_board_margin(self):
        layout = page_layout((760, 820))
        origin = (
            layout.board.left + layout.padding,
            layout.board.top + layout.padding,
        )
        self.assertEqual(position_at_point(layout, origin), (0, 0))
        center = (
            origin[0] + 7 * layout.spacing,
            origin[1] + 7 * layout.spacing,
        )
        self.assertEqual(position_at_point(layout, center), (7, 7))
        self.assertIsNone(position_at_point(layout, layout.board.topleft))

    def test_game_and_mode_selection_render_at_minimum_size(self):
        pygame.font.init()
        screen = pygame.Surface((620, 600))
        state = place_stone(new_game(), (7, 7)).state
        layout = draw_game(screen, state)
        self.assertTrue(screen.get_rect().contains(layout.board))
        draw_game(screen, state, mode_selecting=True)


if __name__ == "__main__":
    unittest.main()
