import unittest

from games.game_aircraft.logic import Transition, new_game
from games.game_aircraft.sound import GameSounds


class RecordingBank:
    def __init__(self):
        self.played = []

    def play(self, name, gain=1.0):
        self.played.append(name)


class AircraftSoundTests(unittest.TestCase):
    def test_boss_and_elite_events_use_distinct_effects(self):
        sounds = GameSounds.__new__(GameSounds)
        sounds.bank = RecordingBank()
        state = new_game()
        sounds.play_transition(Transition(state, ("boss_warning",)))
        sounds.play_transition(Transition(state, ("destroyed", "elite_destroyed")))
        sounds.play_transition(Transition(state, ("destroyed", "boss_defeated")))
        self.assertEqual(
            sounds.bank.played,
            ["boss_warning", "elite_destroyed", "boss_defeated"],
        )


if __name__ == "__main__":
    unittest.main()
