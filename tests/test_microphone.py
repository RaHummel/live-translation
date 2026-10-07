import asyncio
import unittest
from unittest.mock import MagicMock, patch

from config.model.config_models import InputSettings
from sound_inputs.microphone import Microphone


class TestMicrophone(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.input_settings = InputSettings(
            input_device='default', input_device_index=0, input_sample_rate=16000, input_channels=1
        )
        self.device_patcher = patch(
            'sound_inputs.microphone.get_audio_device',
            return_value={'index': 0, 'name': 'default_mic', 'max_input_channels': 2},
        )
        self.stream_patcher = patch('sound_inputs.microphone.sounddevice.RawInputStream')
        self.mock_get_device = self.device_patcher.start()
        self.mock_stream_class = self.stream_patcher.start()
        self.addCleanup(self.device_patcher.stop)
        self.addCleanup(self.stream_patcher.stop)
        self.microphone = Microphone(self.input_settings)

    async def test_get_audio_stream(self):
        mock_stream = MagicMock()
        self.mock_stream_class.return_value = mock_stream
        shutdown_event = asyncio.Event()
        await self.microphone._input_queue.put(b'audio_chunk')
        generator = self.microphone.get_audio_stream(shutdown_event)

        item = await generator.__anext__()
        shutdown_event.set()
        await self.microphone._input_queue.put(b'stop')

        self.assertEqual(item, b'audio_chunk')
        with self.assertRaises(StopAsyncIteration):
            await generator.__anext__()
        mock_stream.start.assert_called_once()

    async def test_get_audio_stream_cancel(self):
        mock_stream = MagicMock()
        self.mock_stream_class.return_value = mock_stream
        shutdown_event = asyncio.Event()
        generator = self.microphone.get_audio_stream(shutdown_event)

        async def run_gen():
            async for _ in generator:
                pass

        task = asyncio.create_task(run_gen())
        await asyncio.sleep(0.01)
        task.cancel()
        await task

        mock_stream.start.assert_called_once()

    def test_stop_audio_stream(self):
        mock_stream = MagicMock()
        self.microphone._audio_stream = mock_stream

        self.microphone.stop_audio_stream()

        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()

    def test_stop_audio_stream_without_stream(self):
        self.microphone._audio_stream = None
        self.microphone.stop_audio_stream()

    def test_callback_schedules_copied_data(self):
        self.microphone._loop = MagicMock()

        result = self.microphone._callback(bytearray(b'data'))

        self.assertIsNone(result)
        self.microphone._loop.call_soon_threadsafe.assert_called_once_with(self.microphone._enqueue_audio, b'data')

    def test_enqueue_audio_drops_chunk_when_queue_is_full(self):
        self.microphone._input_queue = asyncio.Queue(maxsize=1)
        self.microphone._input_queue.put_nowait(b'existing')

        self.microphone._enqueue_audio(b'data')

        self.assertEqual(self.microphone._input_queue.qsize(), 1)
        self.assertEqual(self.microphone._input_queue.get_nowait(), b'existing')

    def test_callback_without_event_loop_drops_data(self):
        self.microphone._loop = None
        self.assertIsNone(self.microphone._callback(b'data'))

    def test_get_input_device_delegates_to_shared_device_service(self):
        self.microphone._get_input_device(99)
        self.mock_get_device.assert_called_with(99, 'input')

    def test_list_input_devices(self):
        expected = [{'name': 'mic1', 'index': 0, 'max_input_channels': 1}]
        with patch('sound_inputs.microphone.list_audio_devices', return_value=expected):
            self.assertEqual(Microphone.list_input_devices(), expected)

    def test_rejects_more_channels_than_device_supports(self):
        self.input_settings.input_channels = 3
        with self.assertRaisesRegex(ValueError, 'supports 2 channels'):
            Microphone(self.input_settings)

    def test_uses_100ms_input_buffer_for_lower_latency(self):
        self.assertEqual(self.microphone._buffer_frames, 1600)
