import asyncio
import logging
import time
from typing import Awaitable, Callable, Dict, Iterable, Optional, Set

from config.model.config_models import SegmentationSettings
from translators.segmenter import TranscriptSegmenter
from translators.translation_callbacks import TranslationCallbacks

LOGGER = logging.getLogger(__name__)

# Backlog below this is considered "in sync" -> normal speaking rate.
BACKLOG_TOLERANCE_S = 1.0
# Rough speech rate used to estimate audio duration of segments not yet synthesized.
ESTIMATED_WORDS_PER_SECOND = 2.5

SpeakCallable = Callable[[str, str], Awaitable[None]]


class SegmentPipeline:
    """Provider independent path from STT transcripts to ordered translation + TTS output.

    * Interim/final transcripts are cut into segments by a :class:`TranscriptSegmenter`
      (or passed through as finals only, if interim segmentation is disabled).
    * Every segment is queued per target language and handed to ``speak(text, language)``
      strictly in order, so audio of consecutive segments never interleaves.
    * The pending audio per language (backlog) is tracked to derive a speaking rate that
      lets the output catch up with fast speakers.
    """

    def __init__(
        self,
        settings: SegmentationSettings,
        target_languages: Iterable[str],
        speak: SpeakCallable,
        translation_callbacks: Optional[TranslationCallbacks] = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._settings = settings
        self._target_languages = list(target_languages)
        self._speak = speak
        self._translation_callbacks = translation_callbacks
        self._clock = clock

        self._segmenter = self._create_segmenter()
        self._queues: Dict[str, asyncio.Queue[str]] = {}
        self._workers: Dict[str, asyncio.Task] = {}
        self._pending_words: Dict[str, int] = {}
        self._playout_end: Dict[str, float] = {}
        self._speaking_rate_unsupported: Set[str] = set()

    @property
    def uses_interim_results(self) -> bool:
        return self._segmenter is not None

    # -- Transcript input ------------------------------------------------------------------------

    def reset(self) -> None:
        """Starts a new utterance, e.g. after the STT stream was restarted."""
        if self._segmenter is not None:
            self._segmenter.reset()

    def on_interim(self, transcript: str) -> None:
        if self._segmenter is None or not transcript.strip():
            return
        LOGGER.debug(f'Interim transcript received: {transcript}')
        for segment in self._segmenter.update_interim(transcript):
            self.dispatch(segment)

    def on_final(self, transcript: str) -> None:
        """Ends the current utterance"""
        if not transcript.strip():
            # An empty final still ends the utterance; otherwise the committed word count
            # would leak into the next utterance and swallow its first words.
            self.reset()
            return
        LOGGER.debug(f'Final transcript received: {transcript}')
        if self._segmenter is None:
            self.dispatch(transcript)
            return
        for segment in self._segmenter.finalize(transcript):
            self.dispatch(segment)

    def dispatch(self, text: str) -> None:
        """Hands a committed source segment to every target language pipeline in order."""
        text = text.strip()
        if not text:
            return
        LOGGER.debug(f'Dispatching segment: {text}')
        if self._translation_callbacks is not None:
            self._translation_callbacks.update_source_field(text)

        word_count = len(text.split())
        for language in self._target_languages:
            queue = self._ensure_worker(language)
            self._pending_words[language] = self._pending_words.get(language, 0) + word_count
            queue.put_nowait(text)

    def start(self) -> None:
        """Starts one worker per target language. Must be called within the running event loop."""
        for language in self._target_languages:
            self._ensure_worker(language)

    async def join(self) -> None:
        """Waits until every queued segment has been processed."""
        await asyncio.gather(*(queue.join() for queue in self._queues.values()))

    async def stop(self, drain_timeout: float = 0.0) -> None:
        """Stops all workers, optionally giving queued segments ``drain_timeout`` seconds to finish."""
        if drain_timeout > 0 and self._queues:
            try:
                await asyncio.wait_for(self.join(), timeout=drain_timeout)
            except asyncio.TimeoutError:
                LOGGER.debug('Segment queues not drained in time, cancelling workers.')

        workers = list(self._workers.values())
        for worker in workers:
            worker.cancel()

        if workers:
            await asyncio.gather(*workers, return_exceptions=True)
        self._workers.clear()
        self._queues.clear()
        self._pending_words.clear()
        self._playout_end.clear()
        self.reset()

    def speaking_rate_for(self, language: str) -> float:
        """Speaking rate the next segment of ``language`` should be synthesized with."""
        if language in self._speaking_rate_unsupported:
            return 1.0

        backlog_s = self.backlog_seconds(language)
        rate = self.speaking_rate_for_backlog(backlog_s)

        return rate

    def disable_speaking_rate(self, language: str) -> None:
        """Disables rate control for a language, e.g. when its voice rejects rate changes."""
        self._speaking_rate_unsupported.add(language)

    def speaking_rate_disabled(self, language: str) -> bool:
        return language in self._speaking_rate_unsupported

    def backlog_seconds(self, language: str) -> float:
        """Audio still to be played (scheduled) plus an estimate for queued, unsynthesized segments."""
        scheduled = max(0.0, self._playout_end.get(language, 0.0) - self._clock())
        queued = self._pending_words.get(language, 0) / ESTIMATED_WORDS_PER_SECOND
        return scheduled + queued

    def speaking_rate_for_backlog(self, backlog_s: float) -> float:
        """Maps the backlog linearly to a speaking rate between 1.0 and ``max_speaking_rate``."""
        span = self._settings.max_backlog_s - BACKLOG_TOLERANCE_S
        if backlog_s <= BACKLOG_TOLERANCE_S or span <= 0:
            return 1.0
        ratio = min(1.0, (backlog_s - BACKLOG_TOLERANCE_S) / span)
        return round(1.0 + (self._settings.max_speaking_rate - 1.0) * ratio, 2)

    def register_playout(self, language: str, duration_s: float) -> None:
        """Advances the expected end of playback; outputs return before the audio is actually played."""
        start = max(self._clock(), self._playout_end.get(language, 0.0))
        self._playout_end[language] = start + duration_s

    # -- Internals -------------------------------------------------------------------------------

    def _create_segmenter(self) -> Optional[TranscriptSegmenter]:
        if not self._settings.use_interim_segmentation:
            return None
        return TranscriptSegmenter(
            min_words=self._settings.min_segment_words,
            max_words=self._settings.max_segment_words,
        )

    def _ensure_worker(self, language: str) -> asyncio.Queue[str]:
        queue = self._queues.get(language)
        if queue is None:
            queue = asyncio.Queue()
            self._queues[language] = queue
        worker = self._workers.get(language)
        if worker is None or worker.done():
            self._workers[language] = asyncio.create_task(self._worker(language, queue))
        return queue

    async def _worker(self, language: str, queue: asyncio.Queue[str]) -> None:
        """Processes the segments of one language strictly in order."""
        while True:
            text = await queue.get()
            self._pending_words[language] = max(0, self._pending_words.get(language, 0) - len(text.split()))
            try:
                await self._speak(text, language)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                LOGGER.error(f'Error while processing segment for {language}: {e}', exc_info=True)
            finally:
                queue.task_done()
