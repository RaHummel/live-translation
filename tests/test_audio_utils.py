import logging
import unittest
from array import array

from utils.audio_utils import pcm_duration_seconds, tail_pause_seconds, trim_silence

SAMPLE_RATE = 1000  # 1 sample == 1 ms


def _samples(pcm: bytes) -> array:
    result = array('h')
    result.frombytes(pcm)
    return result


class TestTailPauseSeconds(unittest.TestCase):
    def test_sentence_end(self):
        for text in ('Done.', 'Really?', 'Wow!', 'And so…'):
            self.assertAlmostEqual(tail_pause_seconds(text), 0.30, msg=text)

    def test_clause_end(self):
        for text in ('First,', 'Note;', 'As follows:'):
            self.assertAlmostEqual(tail_pause_seconds(text), 0.15, msg=text)

    def test_mid_sentence_cut(self):
        self.assertAlmostEqual(tail_pause_seconds('and then we'), 0.05)
        self.assertAlmostEqual(tail_pause_seconds(''), 0.05)

    def test_ignores_trailing_quotes_brackets_and_whitespace(self):
        self.assertAlmostEqual(tail_pause_seconds('He said "stop."  '), 0.30)
        self.assertAlmostEqual(tail_pause_seconds('»Ja!«'), 0.30)
        self.assertAlmostEqual(tail_pause_seconds('(see above,)'), 0.15)

    def test_scales_with_speaking_rate(self):
        self.assertAlmostEqual(tail_pause_seconds('Done.', speaking_rate=1.4), 0.30 / 1.4)
        self.assertAlmostEqual(tail_pause_seconds('Done.', speaking_rate=2.0), 0.15)

    def test_never_lengthens_pause_below_normal_rate(self):
        self.assertAlmostEqual(tail_pause_seconds('Done.', speaking_rate=0.5), 0.30)


class TestTrimSilence(unittest.TestCase):
    voice = array('h', [1000, -1000] * 50)

    def test_trims_lead_to_40ms_and_tail_to_target(self):
        silence = array('h', [0] * 1000)
        pcm = (silence + self.voice + silence).tobytes()

        trimmed = _samples(trim_silence(pcm, SAMPLE_RATE, tail_s=0.3))

        self.assertEqual(len(trimmed), 40 + len(self.voice) + 300)
        self.assertEqual(trimmed[40:140], self.voice)

    def test_keeps_shorter_existing_silence_without_padding(self):
        pcm = (array('h', [0] * 10) + self.voice + array('h', [0] * 20)).tobytes()

        trimmed = _samples(trim_silence(pcm, SAMPLE_RATE, tail_s=0.15))

        self.assertEqual(len(trimmed), 10 + len(self.voice) + 20)

    def test_quiet_samples_below_threshold_count_as_silence(self):
        pcm = (array('h', [150, -150] * 100) + self.voice + array('h', [199] * 100)).tobytes()

        trimmed = _samples(trim_silence(pcm, SAMPLE_RATE, tail_s=0.05))

        self.assertEqual(len(trimmed), 40 + len(self.voice) + 50)

    def test_fully_silent_or_empty_audio_returns_empty(self):
        self.assertEqual(trim_silence(array('h', [0] * 1000).tobytes(), SAMPLE_RATE, tail_s=0.3), b'')
        self.assertEqual(trim_silence(b'', SAMPLE_RATE, tail_s=0.3), b'')
        self.assertEqual(trim_silence(b'\x00', SAMPLE_RATE, tail_s=0.3), b'')

    def test_ignores_odd_trailing_byte(self):
        pcm = self.voice.tobytes() + b'\x01'

        trimmed = _samples(trim_silence(pcm, SAMPLE_RATE, tail_s=0.0))

        self.assertEqual(trimmed, self.voice)

    def test_logs_removed_and_padded_milliseconds(self):
        pcm = (array('h', [0] * 500) + self.voice + array('h', [0] * 500)).tobytes()

        with self.assertLogs('utils.audio_utils', level=logging.DEBUG) as logs:
            trim_silence(pcm, SAMPLE_RATE, tail_s=0.3)

        self.assertIn('removed 460 ms lead / 200 ms tail (target tail 300 ms)', logs.output[0])


class TestPcmDuration(unittest.TestCase):
    def test_duration(self):
        self.assertAlmostEqual(pcm_duration_seconds(b'\x00\x00' * 16000, 16000), 1.0)
