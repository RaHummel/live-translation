from typing import Callable, List

SENTENCE_TERMINATORS = ('.', '?', '!', ';', '…')
CLAUSE_TERMINATORS = (',', ':')
_TRAILING_CLOSERS = '"\'»«“”’)]}'


def _strip_closers(word: str) -> str:
    return word.rstrip(_TRAILING_CLOSERS)


def _is_sentence_end(word: str) -> bool:
    core = _strip_closers(word)
    if not core.endswith(SENTENCE_TERMINATORS):
        return False
    # Ordinals like "3." (e.g. "3. Oktober") are not sentence ends.
    return not core.rstrip('.').isdigit()


def _is_clause_end(word: str) -> bool:
    return _strip_closers(word).endswith(CLAUSE_TERMINATORS)


class TranscriptSegmenter:
    """Cuts a stream of interim STT transcripts into segments that are sent early.

    Once a segment is emitted it is never revised (no re-speak). Committed progress
    within the current utterance is tracked as a word count; later interim revisions
    of already committed words are ignored.

    Rules (evaluated on the uncommitted part of the current utterance):
      * Punctuation: a sentence terminator within the stable part and at least
        ``min_words`` words -> emit everything up to the last terminator as one
        segment (several complete sentences are sent together).
      * Max words: ``max_words`` or more pending words -> emit up to the last clause
        boundary (comma/colon) if it yields at least ``min_words``, otherwise
        everything except the hold-back words.
      * Final: emit the remaining suffix as one segment and reset.

    The last ``holdback_words`` words of an interim are not emitted because the
    recognizer frequently revises them, unless the interim itself ends with a
    sentence terminator (complete sentence -> emit immediately).
    """

    def __init__(self, min_words: int = 5, max_words: int = 14, holdback_words: int = 2):
        if min_words < 1:
            raise ValueError('min_words must be >= 1')
        if max_words <= min_words:
            raise ValueError('max_words must be greater than min_words')
        self._min_words = min_words
        self._max_words = max_words
        self._holdback_words = max(0, holdback_words)
        self._committed_words = 0

    @property
    def committed_words(self) -> int:
        return self._committed_words

    def reset(self) -> None:
        self._committed_words = 0

    def update_interim(self, transcript: str) -> List[str]:
        """Feeds a new interim transcript of the current utterance. Returns segments to emit."""
        pending = transcript.split()[self._committed_words :]
        if not pending:
            return []

        if _is_sentence_end(pending[-1]) or not self._holdback_words:
            # Interim ends with a complete sentence -> no need to wait for further words.
            stable_part = pending
        else:
            stable_part = pending[: len(pending) - self._holdback_words]
        if not stable_part:
            return []

        sentence_cut = self._last_boundary(stable_part, _is_sentence_end)
        if sentence_cut >= self._min_words:
            return [self._commit(pending[:sentence_cut])]

        if len(pending) >= self._max_words:
            clause_cut = self._last_boundary(stable_part, _is_clause_end)
            if clause_cut < self._min_words:
                clause_cut = len(stable_part)
            return [self._commit(pending[:clause_cut])]

        return []

    def finalize(self, transcript: str) -> List[str]:
        """Feeds the final transcript of the current utterance, emits the uncommitted suffix and resets."""
        suffix = transcript.split()[self._committed_words :]
        self.reset()
        return [' '.join(suffix)] if suffix else []

    def _commit(self, words: List[str]) -> str:
        self._committed_words += len(words)
        return ' '.join(words)

    @staticmethod
    def _last_boundary(words: List[str], predicate: Callable[[str], bool]) -> int:
        """Returns the number of words up to and including the last boundary word, or 0."""
        for index in range(len(words) - 1, -1, -1):
            if predicate(words[index]):
                return index + 1
        return 0
