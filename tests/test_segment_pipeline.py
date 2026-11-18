import asyncio
import unittest
from unittest.mock import MagicMock

from config.model.config_models import SegmentationSettings
from translators.segment_pipeline import SegmentPipeline


class TestSegmentPipeline(unittest.IsolatedAsyncioTestCase):
    def _build(self, settings=None, languages=('en-US',), speak=None, callbacks=None, clock=None):
        self.spoken = []

        async def record(text, language):
            self.spoken.append((text, language))

        kwargs = {'clock': clock} if clock is not None else {}
        return SegmentPipeline(
            settings=settings or SegmentationSettings(min_segment_words=5, max_segment_words=14),
            target_languages=languages,
            speak=speak or record,
            translation_callbacks=callbacks,
            **kwargs,
        )

    async def test_interim_and_final_are_segmented_without_respeak(self):
        callbacks = MagicMock()
        pipeline = self._build(callbacks=callbacks)

        pipeline.on_interim('This is the first sentence. And then')
        pipeline.on_interim('This is a first sentence. And then it goes on')
        pipeline.on_final('This is a first sentence. And then it goes on.')
        await asyncio.wait_for(pipeline.join(), timeout=1)
        await pipeline.stop()

        self.assertEqual(
            self.spoken,
            [('This is the first sentence.', 'en-US'), ('And then it goes on.', 'en-US')],
        )
        self.assertEqual(
            [c.args[0] for c in callbacks.update_source_field.call_args_list],
            ['This is the first sentence.', 'And then it goes on.'],
        )

    async def test_without_interim_segmentation_only_finals_are_sent(self):
        pipeline = self._build(settings=SegmentationSettings(use_interim_segmentation=False))
        self.assertFalse(pipeline.uses_interim_results)

        pipeline.on_interim('A very long sentence. Even more words')
        pipeline.on_final('Hello world')
        await asyncio.wait_for(pipeline.join(), timeout=1)
        await pipeline.stop()

        self.assertEqual(self.spoken, [('Hello world', 'en-US')])

    async def test_reset_starts_new_utterance(self):
        pipeline = self._build()
        pipeline.on_interim('This is the first sentence. And then')
        pipeline.reset()
        pipeline.on_final('New sentence')
        await asyncio.wait_for(pipeline.join(), timeout=1)
        await pipeline.stop()

        self.assertEqual([text for text, _ in self.spoken], ['This is the first sentence.', 'New sentence'])

    async def test_segments_are_sent_to_every_target_language(self):
        pipeline = self._build(languages=('en-US', 'fr-FR'))
        pipeline.dispatch('Hello')
        await asyncio.wait_for(pipeline.join(), timeout=1)
        await pipeline.stop()

        self.assertCountEqual(self.spoken, [('Hello', 'en-US'), ('Hello', 'fr-FR')])

    async def test_segments_are_processed_in_order(self):
        processed = []

        async def slow_first(text, _language):
            if text == 'one':
                await asyncio.sleep(0.05)
            processed.append(text)

        pipeline = self._build(speak=slow_first)
        for text in ('one', 'two', 'three'):
            pipeline.dispatch(text)

        await asyncio.wait_for(pipeline.join(), timeout=1)
        await pipeline.stop()

        self.assertEqual(processed, ['one', 'two', 'three'])

    async def test_speak_errors_do_not_stop_the_worker(self):
        processed = []

        async def failing_first(text, _language):
            if text == 'one':
                raise RuntimeError('boom')
            processed.append(text)

        pipeline = self._build(speak=failing_first)
        pipeline.dispatch('one')
        pipeline.dispatch('two')
        await asyncio.wait_for(pipeline.join(), timeout=1)
        await pipeline.stop()

        self.assertEqual(processed, ['two'])

    async def test_stop_drains_queue_within_timeout(self):
        processed = []

        async def slow(text, _language):
            await asyncio.sleep(0.01)
            processed.append(text)

        pipeline = self._build(speak=slow)
        pipeline.dispatch('one')
        pipeline.dispatch('two')
        await pipeline.stop(drain_timeout=1)

        self.assertEqual(processed, ['one', 'two'])

    async def test_stop_without_drain_cancels_pending_segments(self):
        started = asyncio.Event()

        async def blocking(_text, _language):
            started.set()
            await asyncio.Future()

        pipeline = self._build(speak=blocking)
        pipeline.dispatch('one')
        await asyncio.wait_for(started.wait(), timeout=1)
        await asyncio.wait_for(pipeline.stop(), timeout=1)

    def test_speaking_rate_scales_with_backlog(self):
        pipeline = self._build(settings=SegmentationSettings(max_speaking_rate=1.4, max_backlog_s=5.0))

        self.assertEqual(pipeline.speaking_rate_for_backlog(0.0), 1.0)
        self.assertEqual(pipeline.speaking_rate_for_backlog(1.0), 1.0)
        self.assertEqual(pipeline.speaking_rate_for_backlog(3.0), 1.2)
        self.assertEqual(pipeline.speaking_rate_for_backlog(5.0), 1.4)
        self.assertEqual(pipeline.speaking_rate_for_backlog(30.0), 1.4)

    def test_backlog_combines_scheduled_audio_and_pending_words(self):
        now = [100.0]
        pipeline = self._build(clock=lambda: now[0])

        pipeline.register_playout('en-US', 2.0)
        pipeline.register_playout('en-US', 3.0)  # queued after the first one
        pipeline._pending_words['en-US'] = 5  # 5 words / 2.5 wps = 2s

        self.assertAlmostEqual(pipeline.backlog_seconds('en-US'), 7.0)
        now[0] = 104.0
        self.assertAlmostEqual(pipeline.backlog_seconds('en-US'), 3.0)
        now[0] = 200.0
        self.assertAlmostEqual(pipeline.backlog_seconds('en-US'), 2.0)

    def test_speaking_rate_for_language_uses_backlog_and_can_be_disabled(self):
        now = [0.0]
        pipeline = self._build(
            settings=SegmentationSettings(max_speaking_rate=1.4, max_backlog_s=5.0), clock=lambda: now[0]
        )
        pipeline.register_playout('en-US', 10.0)

        self.assertEqual(pipeline.speaking_rate_for('en-US'), 1.4)
        self.assertEqual(pipeline.speaking_rate_for('fr-FR'), 1.0)

        pipeline.disable_speaking_rate('en-US')
        self.assertTrue(pipeline.speaking_rate_disabled('en-US'))
        self.assertEqual(pipeline.speaking_rate_for('en-US'), 1.0)
