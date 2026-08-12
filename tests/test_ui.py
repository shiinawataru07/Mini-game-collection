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

    def test_layout_stays_inside_different_window_sizes(self):
        for window_size in ((360, 500), (500, 620), (900, 700)):
            with self.subTest(window_size=window_size):
                width, height = window_size
                layout = page_layout(window_size)
                board = layout["board"]
                settings = layout["settings"]
                self.assertGreaterEqual(board.left, 0)
                self.assertGreaterEqual(board.top, 0)
                self.assertLessEqual(board.right, width)
                self.assertLessEqual(board.bottom, height)
                self.assertLessEqual(settings.right, width)

    def test_settings_controls_stay_inside_dialog(self):
        controls = settings_controls((360, 500))
        modal, close, themes, languages, copy_save, load_save, restart = controls
        for control in (close, copy_save, load_save, restart, *themes.values(), *languages.values()):
            self.assertTrue(modal.contains(control))
        self.assertEqual(set(themes), set(THEMES))
        self.assertEqual(set(languages), {"en", "zh"})


if __name__ == "__main__":
    unittest.main()

