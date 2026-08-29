import unittest

from games.game_sudoku.logic import Transition, new_game
from games.game_sudoku.sound import GameSounds


class RecordingBank:
    def __init__(self):
        self.played = []

    def play(self, name, gain=1.0):
        self.played.append(name)


class SudokuSoundTests(unittest.TestCase):
    def test_transition_sound_priority(self):
        sounds = GameSounds.__new__(GameSounds)
        sounds.bank = RecordingBank()
        state = new_game()
        sounds.play_transition(Transition(state, ("placed",)))
        sounds.play_transition(Transition(state, ("note",)))
        sounds.play_transition(Transition(state, ("placed", "error")))
        sounds.play_transition(Transition(state, ("hint",)))
        sounds.play_transition(Transition(state, ("placed", "won")))
        self.assertEqual(sounds.bank.played, ["place", "note", "error", "hint", "win"])


if __name__ == "__main__":
    unittest.main()
