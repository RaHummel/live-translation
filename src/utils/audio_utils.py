"""Helpers for post-processing synthesized speech (mono, signed 16-bit PCM)."""

import logging
from array import array

LOGGER = logging.getLogger(__name__)

SAMPLE_WIDTH = 2
# int16 amplitude below which a sample counts as silence (~ -44 dBFS).
SILENCE_THRESHOLD = 200
# Kept before the first audible sample; protects soft onsets. The previous segment already brings its pause.
LEAD_PADDING_S = 0.04
# Pause after the last audible sample, depending on how the spoken text ends.
SENTENCE_END_PAUSE_S = 0.30
CLAUSE_END_PAUSE_S = 0.15
MID_SENTENCE_PAUSE_S = 0.05

_SENTENCE_END_CHARS = '.?!…'
_CLAUSE_END_CHARS = ',;:'
_TRAILING_CLOSERS = '"\'»«“”‘’)]} '


def tail_pause_seconds(text: str, speaking_rate: float = 1.0) -> float:
    """Returns the natural pause after ``text``, shortened in proportion to ``speaking_rate``."""
    stripped = text.rstrip(_TRAILING_CLOSERS + '\t\n\r')
    last_char = stripped[-1:] if stripped else ''
    if last_char and last_char in _SENTENCE_END_CHARS:
        pause = SENTENCE_END_PAUSE_S
    elif last_char and last_char in _CLAUSE_END_CHARS:
        pause = CLAUSE_END_PAUSE_S
    else:
        pause = MID_SENTENCE_PAUSE_S
    return pause / max(speaking_rate, 1.0)


def trim_silence(
    raw_pcm: bytes,
    sample_rate: int,
    tail_s: float,
    lead_s: float = LEAD_PADDING_S,
) -> bytes:
    """Normalizes leading/trailing silence of mono int16 PCM.

    Keeps at most ``lead_s`` of silence before the first audible sample and at most ``tail_s`` after the
    last one. Returns ``b''`` if the audio is entirely silent.
    """
    usable = len(raw_pcm) - (len(raw_pcm) % SAMPLE_WIDTH)
    samples = array('h')
    samples.frombytes(raw_pcm[:usable])
    if not samples:
        return b''

    first = next((i for i, s in enumerate(samples) if abs(s) >= SILENCE_THRESHOLD), None)
    if first is None:
        return b''
    last = next(i for i in range(len(samples) - 1, -1, -1) if abs(samples[i]) >= SILENCE_THRESHOLD)

    lead = int(sample_rate * lead_s)
    tail = int(sample_rate * tail_s)
    start = max(0, first - lead)
    end = min(len(samples), last + 1 + tail)

    if LOGGER.isEnabledFor(logging.DEBUG):
        removed_lead_ms = start * 1000 / sample_rate
        removed_tail_ms = (len(samples) - end) * 1000 / sample_rate
        LOGGER.debug(
            f'Silence trim: removed {removed_lead_ms:.0f} ms lead / {removed_tail_ms:.0f} ms tail '
            f'(target tail {tail_s * 1000:.0f} ms)'
        )

    return samples[start:end].tobytes()


def pcm_duration_seconds(raw_pcm: bytes, sample_rate: int) -> float:
    return len(raw_pcm) / (SAMPLE_WIDTH * sample_rate)
