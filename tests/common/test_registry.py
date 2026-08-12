"""Tests for declarative game registration."""

import unittest
from dataclasses import replace

from games.registry import (
    GAMES,
    _validate_registry,
    game_by_id,
    game_by_shortcut,
)


class GameRegistryTests(unittest.TestCase):
    def test_ids_and_shortcuts_are_unique(self):
        self.assertEqual(len({game.id for game in GAMES}), len(GAMES))
        self.assertEqual(len({game.shortcut for game in GAMES}), len(GAMES))

    def test_games_can_be_looked_up_and_load_their_runner(self):
        for game in GAMES:
            with self.subTest(game=game.id):
                self.assertIs(game_by_id(game.id), game)
                self.assertIs(game_by_shortcut(game.shortcut), game)
                self.assertTrue(callable(game.load_runner()))

    def test_unknown_game_id_has_a_clear_error(self):
        with self.assertRaisesRegex(ValueError, "Unknown game"):
            game_by_id("missing")

    def test_duplicate_registration_is_rejected(self):
        duplicate = replace(GAMES[0], shortcut=GAMES[1].shortcut)
        with self.assertRaisesRegex(ValueError, "shortcuts"):
            _validate_registry((GAMES[1], duplicate))


if __name__ == "__main__":
    unittest.main()
