import asyncio
import io
import sys
import unittest
from array import array
from unittest.mock import patch

from config.model.config_models import MumbleSettings, OutputSettings, SpeakerSettings
from sound_outputs.speaker import Speaker, SpeakerRouter, create_speaker_outputs


class TestSpeaker(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.output_settings = OutputSettings(
            output_method='speaker',
            output_sample_rate=16000,
            chunk_len=4,
            speaker_settings=SpeakerSettings(
                output_device='default', output_device_index=0, language_channel_mapping={'de-DE': 1, 'en-US': 2}
            ),
            mumble_settings=MumbleSettings(ip_address='localhost', port=64738, language_channel_mapping={}),
        )
        self.device_patcher = patch(
            'sound_outputs.speaker.get_audio_device',
            return_value={'index': 0, 'name': 'default_spk', 'max_output_channels': 4},
        )
        self.stream_patcher = patch('sound_outputs.speaker.sounddevice.RawOutputStream')
        self.mock_get_device = self.device_patcher.start()
        self.mock_stream_class = self.stream_patcher.start()
        self.addCleanup(self.device_patcher.stop)
        self.addCleanup(self.stream_patcher.stop)

    def _router(self, mapping=None):
        router = SpeakerRouter(self.output_settings, mapping or {'de-DE': 1, 'en-US': 2})
        self.addCleanup(router.stop)
        return router

    async def test_play_opens_one_shared_stream_and_queues_pcm(self):
        outputs = create_speaker_outputs(self.output_settings, ['de-DE', 'en-US'])
        router = outputs['de-DE']._router
        self.addCleanup(router.stop)

        await asyncio.gather(
            outputs['de-DE'].play(io.BytesIO(array('h', [1, 2]).tobytes())),
            outputs['en-US'].play(io.BytesIO(array('h', [10, 20]).tobytes())),
        )

        self.mock_stream_class.assert_called_once()
        self.mock_stream_class.return_value.start.assert_called_once()
        self.assertIs(outputs['de-DE']._router, outputs['en-US']._router)

    def test_callback_routes_each_language_to_its_physical_channel(self):
        router = self._router()
        router._queues['de-DE'].put(array('h', [1, 2, 3]).tobytes())
        router._queues['en-US'].put(array('h', [10, 20, 30]).tobytes())
        output = bytearray(3 * 2 * 2)

        router._audio_callback(output, 3)

        samples = array('h')
        samples.frombytes(output)
        self.assertEqual(samples.tolist(), [1, 10, 2, 20, 3, 30])

    def test_callback_uses_silence_on_language_underrun(self):
        router = self._router()
        router._queues['de-DE'].put(array('h', [1]).tobytes())
        output = bytearray(2 * 2 * 2)

        router._audio_callback(output, 2)

        samples = array('h')
        samples.frombytes(output)
        self.assertEqual(samples.tolist(), [1, 0, 0, 0])

    def test_partial_chunks_are_preserved_between_callbacks(self):
        router = self._router({'de-DE': 1})
        router._queues['de-DE'].put(array('h', [1, 2, 3]).tobytes())
        first = bytearray(2 * 2)
        second = bytearray(2 * 2)

        router._audio_callback(first, 2)
        router._audio_callback(second, 2)

        first_samples = array('h')
        first_samples.frombytes(first)
        second_samples = array('h')
        second_samples.frombytes(second)
        self.assertEqual(first_samples.tolist(), [1, 2])
        self.assertEqual(second_samples.tolist(), [3, 0])

    def test_rejects_duplicate_or_unavailable_channels(self):
        with self.assertRaisesRegex(ValueError, 'different output channel'):
            SpeakerRouter(self.output_settings, {'de-DE': 1, 'en-US': 1})
        with self.assertRaisesRegex(ValueError, 'supports 4 channels'):
            SpeakerRouter(self.output_settings, {'de-DE': 5})

    def test_single_language_without_mapping_uses_channel_one(self):
        self.output_settings.speaker_settings.language_channel_mapping = {}

        outputs = create_speaker_outputs(self.output_settings, ['de-DE'])
        router = outputs['de-DE']._router
        self.addCleanup(router.stop)

        self.assertEqual(router._language_channel_mapping, {'de-DE': 1})

    def test_multiple_languages_require_complete_mapping(self):
        self.output_settings.speaker_settings.language_channel_mapping = {'de-DE': 1}

        with self.assertRaisesRegex(ValueError, 'en-US'):
            create_speaker_outputs(self.output_settings, ['de-DE', 'en-US'])

    def test_stop_is_idempotent_across_adapters(self):
        outputs = create_speaker_outputs(self.output_settings, ['de-DE', 'en-US'])
        router = outputs['de-DE']._router
        router._ensure_audio_stream_initialized()

        outputs['de-DE'].stop_audio_stream()
        outputs['en-US'].stop_audio_stream()

        self.mock_stream_class.return_value.stop.assert_called_once()
        self.mock_stream_class.return_value.close.assert_called_once()

    def test_list_output_devices(self):
        expected = [{'name': 'spk1', 'index': 0, 'max_output_channels': 2}]
        with patch('sound_outputs.speaker.list_audio_devices', return_value=expected):
            self.assertEqual(Speaker.list_output_devices(), expected)

    def test_pcm_test_assumes_little_endian_host(self):
        self.assertEqual(sys.byteorder, 'little')
