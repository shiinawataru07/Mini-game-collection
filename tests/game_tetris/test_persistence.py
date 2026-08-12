import tempfile
import unittest
from pathlib import Path

from games.game_tetris.persistence import PlayerData, load_player_data, save_player_data


class TetrisPersistenceTests(unittest.TestCase):
    def test_round_trip_records_and_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            expected = PlayerData(12345, 42, "classic", "en")
            self.assertTrue(save_player_data(expected, path))
            self.assertEqual(load_player_data(path), expected)

    def test_invalid_data_falls_back_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            path.write_text('{"best_score": true, "theme": "missing"}', encoding="utf-8")
            data = load_player_data(path)
            self.assertEqual(data.best_score, 0)
            self.assertEqual(data.theme, "midnight")


if __name__ == "__main__":
    unittest.main()
