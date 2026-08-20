import unittest

from games.game_gomoku.logic import MoveResult, new_game
from games.game_gomoku.sound import GameSounds


class RecordingBank:
    def __init__(self):
        self.played = []

    def play(self, name, gain=1.0):
        self.played.append(name)


class GomokuSoundTests(unittest.TestCase):
    def test_move_and_win_use_distinct_effects(self):
        sounds = GameSounds.__new__(GameSounds)
        sounds.bank = RecordingBank()
        state = new_game()
        sounds.play_move(MoveResult(state, placed=False))
        sounds.play_move(MoveResult(state, placed=True))
        sounds.play_move(MoveResult(state, placed=True, won=True))
        sounds.play_undo()
        self.assertEqual(sounds.bank.played, ["stone", "win", "undo"])


if __name__ == "__main__":
    unittest.main()
