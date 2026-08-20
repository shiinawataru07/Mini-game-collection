"""Tests for the data-driven collection menu layout."""

import unittest
from dataclasses import replace

import pygame
from games.menu import menu_layout
from games.registry import GAMES


class MenuLayoutTests(unittest.TestCase):
    def test_registered_cards_are_distinct_and_inside_the_window(self):
        for width, height in ((600, 480), (760, 600), (1200, 800)):
            with self.subTest(window_size=(width, height)):
                layout = menu_layout((width, height))
                cards = list(layout.cards.values())
                self.assertEqual(set(layout.cards), {game.id for game in GAMES})
                self.assertTrue(pygame.Rect(0, 0, width, height).contains(layout.settings))
                for index, card in enumerate(cards):
                    self.assertFalse(any(card.colliderect(other) for other in cards[index + 1 :]))
                    self.assertGreaterEqual(card.left, 0)
                    self.assertGreaterEqual(card.top, 0)
                    self.assertLessEqual(card.right, width)
                    self.assertLessEqual(card.bottom, height)

    def test_grid_expands_without_menu_code_changes(self):
        extra_games = GAMES + (
            replace(GAMES[0], id="third", shortcut=3),
            replace(GAMES[0], id="fourth", shortcut=4),
        )
        layout = menu_layout((600, 480), extra_games)

        self.assertEqual(set(layout.cards), {game.id for game in extra_games})
        self.assertTrue(all(card.bottom <= 480 for card in layout.cards.values()))


if __name__ == "__main__":
    unittest.main()
