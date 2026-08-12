"""Tests for 2048 rules, themes, and responsive layout."""

import json
import tempfile
import unittest
from pathlib import Path

from games.game_2048.game import (
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    TEXTS,
    THEMES,
    _page_layout,
    _settings_controls,
    build_tile_motions,
    load_best_score,
    save_best_score,
)
from games.game_2048.logic import (
    GameState,
    add_random_tile,
    apply_move,
    can_move,
    create_save_json,
    create_empty_board,
    merge_line,
    move_board,
    new_game,
    parse_save_json,
)


class FixedRandom:
    """Predictable random source used by tile-generation tests."""

    def __init__(self, random_value: float = 0.5) -> None:
        self.random_value = random_value

    def choice(self, values):
        return values[0]

    def random(self) -> float:
        return self.random_value


class MergeLineTests(unittest.TestCase):
    def test_common_merge_rules(self):
        cases = [
            ([0, 0, 0, 0], [0, 0, 0, 0], 0),
            ([2, 0, 2, 0], [4, 0, 0, 0], 4),
            ([2, 2, 2, 0], [4, 2, 0, 0], 4),
            ([2, 2, 2, 2], [4, 4, 0, 0], 8),
            ([4, 4, 8, 8], [8, 16, 0, 0], 24),
            ([4, 4, 8, 0], [8, 8, 0, 0], 8),
        ]

        for line, expected, score in cases:
            with self.subTest(line=line):
                self.assertEqual(merge_line(line), (expected, score))


class BoardMovementTests(unittest.TestCase):
    def setUp(self):
        self.board = [
            [2, 2, 0, 0],
            [4, 0, 4, 8],
            [0, 0, 8, 0],
            [0, 4, 0, 8],
        ]

    def test_moves_in_all_directions(self):
        cases = {
            "left": [[4, 0, 0, 0], [8, 8, 0, 0], [8, 0, 0, 0], [4, 8, 0, 0]],
            "right": [[0, 0, 0, 4], [0, 0, 8, 8], [0, 0, 0, 8], [0, 0, 4, 8]],
            "up": [[2, 2, 4, 16], [4, 4, 8, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            "down": [[0, 0, 0, 0], [0, 0, 0, 0], [2, 2, 4, 0], [4, 4, 8, 16]],
        }

        for direction, expected in cases.items():
            with self.subTest(direction=direction):
                moved, _, changed = move_board(self.board, direction)
                self.assertEqual(moved, expected)
                self.assertTrue(changed)

    def test_move_reports_score_without_changing_original(self):
        board = [[2, 2, 4, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

        moved, score, changed = move_board(board, "left")

        self.assertEqual(moved[0], [4, 8, 0, 0])
        self.assertEqual(score, 12)
        self.assertTrue(changed)
        self.assertEqual(board[0], [2, 2, 4, 4])

    def test_invalid_direction_is_rejected(self):
        with self.assertRaises(ValueError):
            move_board(create_empty_board(), "diagonal")


class GameStateTests(unittest.TestCase):
    def test_random_tile_can_be_two_or_four(self):
        board = create_empty_board()

        with_two = add_random_tile(board, FixedRandom(0.5))
        with_four = add_random_tile(board, FixedRandom(0.05))

        self.assertEqual(with_two[0][0], 2)
        self.assertEqual(with_four[0][0], 4)
        self.assertEqual(board[0][0], 0)

    def test_new_game_starts_with_two_tiles(self):
        state = new_game(rng=FixedRandom())

        tiles = [value for row in state.board for value in row if value]
        self.assertEqual(tiles, [2, 2])
        self.assertEqual(state.score, 0)
        self.assertFalse(state.game_over)

    def test_valid_move_adds_one_tile_and_updates_score(self):
        state = GameState(
            board=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=10,
        )

        result = apply_move(state, "left", FixedRandom())

        non_zero_tiles = [value for row in result.board for value in row if value]
        self.assertEqual(sorted(non_zero_tiles), [2, 4])
        self.assertEqual(result.score, 14)

    def test_invalid_move_does_not_add_tile(self):
        state = GameState(
            board=[[2, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        )

        result = apply_move(state, "left", FixedRandom())

        self.assertEqual(result.board, state.board)
        self.assertEqual(result.score, 0)

    def test_game_over_detection(self):
        ended_board = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]
        playable_board = [
            [2, 2, 4, 8],
            [4, 8, 16, 32],
            [8, 16, 32, 64],
            [16, 32, 64, 128],
        ]

        self.assertFalse(can_move(ended_board))
        self.assertTrue(can_move(playable_board))
        self.assertTrue(apply_move(GameState(ended_board), "left").game_over)

    def test_new_game_can_be_used_to_restart(self):
        finished = GameState([[2, 4], [4, 2]], score=200, game_over=True)

        restarted = new_game(size=2, rng=FixedRandom())

        self.assertNotEqual(restarted, finished)
        self.assertEqual(restarted.score, 0)
        self.assertFalse(restarted.game_over)
        self.assertEqual(sum(value != 0 for row in restarted.board for value in row), 2)


class UiSettingsTests(unittest.TestCase):
    def test_expected_color_themes_are_available(self):
        self.assertEqual(DEFAULT_THEME, "warm")
        self.assertEqual(set(THEMES), {"warm", "blue", "green"})

    def test_english_and_chinese_are_available(self):
        self.assertEqual(DEFAULT_LANGUAGE, "en")
        self.assertEqual(set(TEXTS), {"en", "zh"})
        self.assertEqual(TEXTS["en"]["settings"], "Settings")
        self.assertEqual(TEXTS["zh"]["settings"], "设置")

    def test_layout_stays_inside_different_window_sizes(self):
        for window_size in ((360, 500), (500, 620), (900, 700)):
            with self.subTest(window_size=window_size):
                width, height = window_size
                layout = _page_layout(window_size)
                board = layout["board"]
                settings = layout["settings"]

                self.assertGreaterEqual(board.left, 0)
                self.assertGreaterEqual(board.top, 0)
                self.assertLessEqual(board.right, width)
                self.assertLessEqual(board.bottom, height)
                self.assertLessEqual(settings.right, width)

    def test_settings_controls_stay_inside_dialog(self):
        (
            modal,
            close,
            theme_buttons,
            language_buttons,
            copy_save,
            load_save,
            restart,
        ) = _settings_controls((360, 500))

        self.assertTrue(modal.contains(close))
        self.assertTrue(modal.contains(restart))
        self.assertEqual(set(theme_buttons), set(THEMES))
        self.assertEqual(set(language_buttons), {"en", "zh"})
        for button in theme_buttons.values():
            self.assertTrue(modal.contains(button))
        for button in language_buttons.values():
            self.assertTrue(modal.contains(button))
        self.assertTrue(modal.contains(copy_save))
        self.assertTrue(modal.contains(load_save))


class MoveAnimationTests(unittest.TestCase):
    def test_each_existing_tile_gets_one_motion(self):
        board = [
            [2, 0, 2, 0],
            [4, 8, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 16],
        ]

        for direction in ("up", "down", "left", "right"):
            with self.subTest(direction=direction):
                motions = build_tile_motions(board, direction)
                self.assertEqual(len(motions), 5)

    def test_merging_tiles_share_the_same_destination(self):
        board = [
            [2, 2, 2, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]

        motions = build_tile_motions(board, "left")

        self.assertEqual([motion.start for motion in motions], [(0, 0), (0, 1), (0, 2)])
        self.assertEqual([motion.end for motion in motions], [(0, 0), (0, 0), (0, 1)])


class SaveDataTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState(
            board=[
                [2, 4, 8, 16],
                [32, 64, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0],
            ],
            score=256,
            game_over=False,
        )

    def test_save_json_round_trip_preserves_game_information(self):
        save_text = create_save_json(self.state, 1024, "green", "zh")

        saved = parse_save_json(
            save_text,
            allowed_themes=set(THEMES),
            allowed_languages=set(TEXTS),
        )

        self.assertEqual(saved.state, self.state)
        self.assertEqual(saved.best_score, 1024)
        self.assertEqual(saved.theme, "green")
        self.assertEqual(saved.language, "zh")
        self.assertEqual(json.loads(save_text)["game"], "2048")

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
        save_text = create_save_json(self.state, 10, "warm", "en")
        saved = parse_save_json(save_text)
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
