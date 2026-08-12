"""Tests for Snake player-data persistence."""

import tempfile
import unittest
from pathlib import Path

from games.game_snake.persistence import PlayerData, load_player_data, save_player_data


class SnakePersistenceTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            self.assertTrue(save_player_data(120, "night", "en", path, "fast"))
            self.assertEqual(load_player_data(path), PlayerData(120, "night", "en", "fast"))

    def test_invalid_data_falls_back_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            path.write_text(
                '{"best_score": -2, "theme": "bad", "language": "bad", "speed": "bad"}',
                encoding="utf-8",
            )
            self.assertEqual(load_player_data(path), PlayerData())

    def test_older_player_data_uses_the_default_speed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            path.write_text(
                '{"best_score": 30, "theme": "ocean", "language": "zh"}',
                encoding="utf-8",
            )
            self.assertEqual(load_player_data(path), PlayerData(30, "ocean", "zh", "normal"))


if __name__ == "__main__":
    unittest.main()
