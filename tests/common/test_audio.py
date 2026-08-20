import unittest

from games.common.app_settings import AppSettings
from games.common.audio import SAMPLE_RATE, SoundBank, sequence_samples, tone_samples


class FakeSound:
    def __init__(self):
        self.volume = None
        self.plays = 0

    def set_volume(self, volume):
        self.volume = volume

    def play(self):
        self.plays += 1


class AudioTests(unittest.TestCase):
    def test_tone_length_and_bounds(self):
        samples = tone_samples(440, 100)
        self.assertEqual(len(samples), round(SAMPLE_RATE * 0.1))
        self.assertTrue(all(-1.0 <= sample <= 1.0 for sample in samples))

    def test_sequence_concatenates_notes(self):
        samples = sequence_samples(((440, 50), (660, 100)))
        self.assertEqual(len(samples), round(SAMPLE_RATE * 0.05) + round(SAMPLE_RATE * 0.1))

    def test_sound_bank_applies_live_global_volume(self):
        sound = FakeSound()
        bank = SoundBank.__new__(SoundBank)
        bank.settings = AppSettings(volume=50)
        bank.sounds = {"move": sound}
        bank.play("move", gain=0.5)
        self.assertEqual(sound.volume, 0.25)
        self.assertEqual(sound.plays, 1)

        bank.update_settings(AppSettings(volume=80, muted=True))
        bank.play("move")
        self.assertEqual(sound.plays, 1)


if __name__ == "__main__":
    unittest.main()
