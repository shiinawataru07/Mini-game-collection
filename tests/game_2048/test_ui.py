"""Tests for themes, translations, and responsive control layout."""

import unittest

from games.game_2048.config import (
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    TEXTS,
    THEMES,
)
from games.game_2048.ui import page_layout, settings_controls


class UiSettingsTests(unittest.TestCase):
    def test_expected_color_themes_are_available(self):
        self.assertEqual(DEFAULT_THEME, "warm")
        self.assertEqual(set(THEMES), {"warm", "blue", "green"})

    def test_english_and_chinese_are_available(self):
        self.assertEqual(DEFAULT_LANGUAGE, "en")
        self.assertEqual(set(TEXTS), {"en", "zh"})
        self.assertEqual(TEXTS["zh"]["settings"], "设置")
        self.assertEqual(TEXTS["en"]["start_ai"], "Start AI")
        self.assertEqual(TEXTS["zh"]["pause_ai"], "暂停 AI")

    def test_layout_stays_inside_different_window_sizes(self):
        for window_size in ((420, 580), (600, 760), (1000, 800)):
            with self.subTest(window_size=window_size):
                width, height = window_size
                layout = page_layout(window_size)
                board = layout["board"]
                settings = layout["settings"]
                ai_toggle = layout["ai_toggle"]
                self.assertGreaterEqual(board.left, 0)
                self.assertGreaterEqual(board.top, 0)
                self.assertLessEqual(board.right, width)
                self.assertLessEqual(board.bottom, height)
                self.assertLessEqual(settings.right, width)
                self.assertLessEqual(ai_toggle.right, width)
                self.assertLessEqual(ai_toggle.bottom, board.top)

    def test_settings_controls_stay_inside_dialog(self):
        for window_size in ((420, 580), (600, 760), (1000, 800)):
            with self.subTest(window_size=window_size):
                controls = settings_controls(window_size)
                clickable = (
                    controls.close,
                    controls.ai_speed,
                    controls.copy_save,
                    controls.load_save,
                    controls.restart,
                    *controls.themes.values(),
                    *controls.languages.values(),
                    *controls.board_sizes.values(),
                )
                for control in clickable:
                    self.assertTrue(controls.modal.contains(control))

                content_controls = clickable[1:]
                for index, control in enumerate(content_controls):
                    for other in content_controls[index + 1 :]:
                        self.assertFalse(control.colliderect(other))

        controls = settings_controls((600, 760))
        self.assertEqual(controls.modal.size, (560, 680))
        self.assertEqual(set(controls.themes), set(THEMES))
        self.assertEqual(set(controls.languages), {"en", "zh"})
        self.assertEqual(set(controls.board_sizes), {3, 4, 5})


if __name__ == "__main__":
    unittest.main()
