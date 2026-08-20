import unittest
from types import SimpleNamespace

from games.game_2048.sound import GameSounds


class RecordingBank:
    def __init__(self):
        self.played = []

    def play(self, name, gain=1.0):
        self.played.append(name)


class Game2048SoundTests(unittest.TestCase):
    def test_merge_and_plain_move_use_different_effects(self):
        sounds = GameSounds.__new__(GameSounds)
        sounds.bank = RecordingBank()
        sounds.play_move(SimpleNamespace(gained_score=0))
        sounds.play_move(SimpleNamespace(gained_score=8))
        sounds.play_game_over()
        self.assertEqual(sounds.bank.played, ["move", "merge", "game_over"])


if __name__ == "__main__":
    unittest.main()
