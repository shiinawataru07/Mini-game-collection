import tempfile
import unittest
from pathlib import Path

from games.game_aircraft.persistence import load_best_score, save_best_score


class AircraftPersistenceTests(unittest.TestCase):
    def test_best_score_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            self.assertTrue(save_best_score(12345, path))
            self.assertEqual(load_best_score(path), 12345)

    def test_invalid_score_falls_back_to_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            path.write_text('{"best_score": true}', encoding="utf-8")
            self.assertEqual(load_best_score(path), 0)


if __name__ == "__main__":
    unittest.main()
