"""Tests for synthesized Minesweeper outcome sounds."""

import unittest

from games.game_minesweeper.sound import (
    SAMPLE_RATE,
    _explosion_samples,
    _victory_samples,
    play_outcome_transition,
)


class RecordingSounds:
    def __init__(self):
        self.victories = 0
        self.explosions = 0

    def play_victory(self):
        self.victories += 1

    def play_explosion(self):
        self.explosions += 1


class SoundSynthesisTests(unittest.TestCase):
    def test_victory_sound_is_a_short_four_note_phrase(self):
        samples = _victory_samples()
        self.assertEqual(len(samples), round(SAMPLE_RATE * 0.12) * 4)
        self.assertTrue(all(-1.0 <= sample <= 1.0 for sample in samples))
        self.assertGreater(max(samples), 0.1)

    def test_explosion_sound_is_bounded_and_fades(self):
        samples = _explosion_samples()
        self.assertEqual(len(samples), round(SAMPLE_RATE * 0.38))
        self.assertTrue(all(-1.0 <= sample <= 1.0 for sample in samples))
        early_energy = sum(abs(sample) for sample in samples[:2000])
        late_energy = sum(abs(sample) for sample in samples[-2000:])
        self.assertGreater(early_energy, late_energy * 10)

    def test_terminal_transitions_play_the_matching_effect_once(self):
        sounds = RecordingSounds()
        play_outcome_transition("running", "lost", sounds)
        play_outcome_transition("lost", "lost", sounds)
        play_outcome_transition("running", "won", sounds)
        play_outcome_transition("won", "won", sounds)
        self.assertEqual(sounds.explosions, 1)
        self.assertEqual(sounds.victories, 1)


if __name__ == "__main__":
    unittest.main()
