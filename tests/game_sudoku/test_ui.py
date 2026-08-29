import unittest

import pygame
from games.game_sudoku.logic import new_game
from games.game_sudoku.ui import (
    cell_at_position,
    draw_game,
    format_time,
    level_controls,
    page_layout,
    settings_controls,
)


class SudokuUiTests(unittest.TestCase):
    def test_layouts_stay_inside_supported_windows(self):
        for size in ((620, 720), (820, 850), (1100, 900)):
            with self.subTest(size=size):
                bounds = pygame.Rect((0, 0), size)
                layout = page_layout(size)
                rects = (
                    layout.board,
                    layout.back,
                    layout.levels,
                    layout.settings,
                    layout.restart,
                    *layout.stats,
                    *layout.numbers.values(),
                    layout.undo,
                    layout.redo,
                    layout.erase,
                    layout.notes,
                    layout.hint,
                    layout.pause,
                )
                self.assertTrue(all(bounds.contains(rect) for rect in rects))
                self.assertEqual(layout.board.width, layout.cell_size * 9)

    def test_overlay_controls_stay_inside_modals(self):
        level = level_controls((620, 720))
        self.assertTrue(
            all(
                level.modal.contains(rect)
                for rect in (*level.difficulties.values(), *level.levels.values())
            )
        )
        settings = settings_controls((620, 720))
        self.assertTrue(
            all(
                settings.modal.contains(rect)
                for rect in (
                    settings.close,
                    *settings.themes.values(),
                    *settings.languages.values(),
                )
            )
        )

    def test_cell_mapping_and_time_format(self):
        layout = page_layout((820, 850))
        self.assertEqual(cell_at_position(layout, layout.board.center), (4, 4))
        self.assertIsNone(cell_at_position(layout, (0, 0)))
        self.assertEqual(format_time(None), "--:--")
        self.assertEqual(format_time(125_000), "02:05")

    def test_game_settings_and_level_selection_render(self):
        pygame.font.init()
        screen = pygame.Surface((620, 720))
        state = new_game("hard", 3)
        draw_game(
            screen,
            state,
            {"easy:1": 32_000},
            "paper",
            "zh",
            level_selecting=True,
            selector_difficulty="easy",
        )
        draw_game(screen, state, {}, "night", "en", settings_open=True)


if __name__ == "__main__":
    unittest.main()
