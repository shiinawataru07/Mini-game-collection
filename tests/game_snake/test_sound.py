import unittest

from games.game_snake.logic import GameState, StepResult
from games.game_snake.sound import GameSounds


class RecordingBank:
    def __init__(self):
        self.played = []

    def play(self, name, gain=1.0):
        self.played.append(name)


def state(status="running"):
    return GameState(8, 6, ((3, 2), (2, 2)), "right", (7, 5), status=status)


class SnakeSoundTests(unittest.TestCase):
    def test_step_outcomes_map_to_effects(self):
        sounds = GameSounds.__new__(GameSounds)
        sounds.bank = RecordingBank()
        sounds.play_step(StepResult(state(), ate_food=True))
        sounds.play_step(StepResult(state(), ate_bonus=True))
        sounds.play_step(StepResult(state("game_over"), collision="wall"))
        sounds.play_step(StepResult(state("won"), ate_food=True))
        self.assertEqual(sounds.bank.played, ["food", "bonus", "collision", "win"])


if __name__ == "__main__":
    unittest.main()
