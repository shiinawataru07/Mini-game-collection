"""Tests for the collection menu layout."""

import unittest

from games.menu import menu_layout


class MenuLayoutTests(unittest.TestCase):
    def test_game_cards_are_distinct_and_inside_the_window(self):
        for width, height in ((600, 480), (760, 600), (1200, 800)):
            with self.subTest(window_size=(width, height)):
                layout = menu_layout((width, height))
                self.assertFalse(layout.game_2048.colliderect(layout.snake))
                for card in (layout.game_2048, layout.snake):
                    self.assertGreaterEqual(card.left, 0)
                    self.assertGreaterEqual(card.top, 0)
                    self.assertLessEqual(card.right, width)
                    self.assertLessEqual(card.bottom, height)


if __name__ == "__main__":
    unittest.main()
