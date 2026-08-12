"""Tests for JSON saves and local best-score persistence."""

import json
import tempfile
import unittest
from pathlib import Path

from games.game_2048.config import TEXTS, THEMES
from games.game_2048.logic import GameState
from games.game_2048.persistence import (
    create_save_json,
    load_best_score,
    parse_save_json,
    save_best_score,
)


class SaveDataTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState(
            [
                [2, 4, 8, 16],
                [32, 64, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
            score=256,
        )

    def test_save_json_round_trip_preserves_game_information(self):
        value = create_save_json(self.state, 1024, "green", "zh")
        saved = parse_save_json(value, set(THEMES), set(TEXTS))
        self.assertEqual(saved.state, self.state)
        self.assertEqual(saved.best_score, 1024)
        self.assertEqual(saved.theme, "green")
        self.assertEqual(saved.language, "zh")
        self.assertEqual(json.loads(value)["game"], "2048")

    def test_invalid_json_and_invalid_tiles_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_save_json("not json")
        payload = json.loads(create_save_json(self.state, 256, "warm", "en"))
        payload["state"]["board"][0][0] = 3
        with self.assertRaises(ValueError):
            parse_save_json(json.dumps(payload))

    def test_wrong_game_and_unsupported_preferences_are_rejected(self):
        payload = json.loads(create_save_json(self.state, 256, "warm", "en"))
        payload["game"] = "snake"
        with self.assertRaises(ValueError):
            parse_save_json(json.dumps(payload))
        payload["game"] = "2048"
        payload["preferences"]["theme"] = "unknown"
        with self.assertRaises(ValueError):
            parse_save_json(json.dumps(payload), allowed_themes=set(THEMES))

    def test_best_score_never_falls_below_current_score(self):
        saved = parse_save_json(create_save_json(self.state, 10, "warm", "en"))
        self.assertEqual(saved.best_score, self.state.score)

    def test_best_score_is_persisted_locally(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.json"
            self.assertEqual(load_best_score(path), 0)
            self.assertTrue(save_best_score(4096, path))
            self.assertEqual(load_best_score(path), 4096)
            path.write_text("broken", encoding="utf-8")
            self.assertEqual(load_best_score(path), 0)


if __name__ == "__main__":
    unittest.main()

