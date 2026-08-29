import tempfile
import unittest
from pathlib import Path

from games.game_sudoku.persistence import (
    PlayerData,
    load_player_data,
    record_completion,
    save_player_data,
)


class SudokuPersistenceTests(unittest.TestCase):
    def test_round_trip_progress_and_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            expected = PlayerData({"easy:1": 42_000}, "night", "en", "hard", 4)
            self.assertTrue(save_player_data(expected, path))
            self.assertEqual(load_player_data(path), expected)

    def test_invalid_data_falls_back_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            path.write_text(
                '{"best_times_ms":{"hard:99":12,"easy:1":true},"difficulty":"bad"}',
                encoding="utf-8",
            )
            self.assertEqual(load_player_data(path), PlayerData())

    def test_record_keeps_fastest_time(self):
        data = record_completion(PlayerData(), "easy", 0, 50_000)
        self.assertEqual(data.best_times_ms["easy:1"], 50_000)
        self.assertIs(record_completion(data, "easy", 0, 60_000), data)
        faster = record_completion(data, "easy", 0, 40_000)
        self.assertEqual(faster.best_times_ms["easy:1"], 40_000)


if __name__ == "__main__":
    unittest.main()
