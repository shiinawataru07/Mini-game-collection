import unittest

from games.game_tetris.logic import Transition, new_game
from games.game_tetris.sound import GameSounds


class RecordingBank:
    def __init__(self):
        self.played = []

    def play(self, name, gain=1.0):
        self.played.append(name)


class TetrisSoundTests(unittest.TestCase):
    def test_transitions_choose_highest_priority_effect(self):
        sounds = GameSounds.__new__(GameSounds)
        sounds.bank = RecordingBank()
        state = new_game()
        sounds.play_transition(Transition(state, ("rotated",)))
        sounds.play_transition(Transition(state, ("held",)))
        sounds.play_transition(Transition(state, ("locked", "lines_cleared"), (20, 21)))
        sounds.play_transition(Transition(state, ("locked", "game_over")))
        self.assertEqual(sounds.bank.played, ["rotate", "hold", "clear_2", "game_over"])


if __name__ == "__main__":
    unittest.main()
