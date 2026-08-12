"""Tests for Minesweeper player-data persistence."""

import tempfile
import unittest
from pathlib import Path

from games.game_minesweeper.persistence import (
    PlayerData,
    load_player_data,
    save_player_data,
    update_best_time,
)


class MinesweeperPersistenceTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            data = PlayerData(
                {"beginner": 12000, "intermediate": None, "expert": 99000},
                "night",
                "en",
                "expert",
            )
            self.assertTrue(save_player_data(data, path))
            self.assertEqual(load_player_data(path), data)

    def test_custom_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            data = PlayerData(
                difficulty="custom",
                custom_width=24,
                custom_height=18,
                custom_mines=85,
            )
            self.assertTrue(save_player_data(data, path))
            self.assertEqual(load_player_data(path), data)

    def test_invalid_custom_settings_are_clamped_on_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            path.write_text(
                '{"difficulty":"custom","custom_width":100,"custom_height":2,"custom_mines":999}',
                encoding="utf-8",
            )
            data = load_player_data(path)
            self.assertEqual(data.difficulty, "custom")
            self.assertEqual((data.custom_width, data.custom_height), (30, 8))
            self.assertEqual(data.custom_mines, 60)

    def test_invalid_data_falls_back_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            path.write_text(
                '{"best_times_ms":{"beginner":-1},"theme":"bad",'
                '"language":"bad","difficulty":"bad"}',
                encoding="utf-8",
            )
            self.assertEqual(load_player_data(path), PlayerData())

    def test_corrupt_file_uses_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            path.write_text("not json", encoding="utf-8")
            self.assertEqual(load_player_data(path), PlayerData())

    def test_best_time_only_keeps_faster_result(self):
        data = update_best_time(PlayerData(), "beginner", 15000)
        slower = update_best_time(data, "beginner", 18000)
        faster = update_best_time(slower, "beginner", 9000)
        self.assertIs(slower, data)
        self.assertEqual(faster.best_times_ms["beginner"], 9000)

    def test_custom_games_do_not_accept_best_time_records(self):
        with self.assertRaises(ValueError):
            update_best_time(PlayerData(difficulty="custom"), "custom", 9000)


if __name__ == "__main__":
    unittest.main()
