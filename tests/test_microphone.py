import asyncio
import unittest
from unittest.mock import MagicMock, patch

import pyaudio

from config.model.config_models import InputSettings
from sound_inputs.microphone import Microphone


class TestMicrophone(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.input_settings = InputSettings(
            input_device='default', input_device_index=0, input_sample_rate=16000, input_channels=1
        )
        self.patcher = patch('pyaudio.PyAudio')
        self.mock_pa = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.mock_pa_instance = self.mock_pa.return_value

        self.mock_pa_instance.get_default_input_device_info.return_value = {
            'index': 0,
            'name': 'default_mic',
            'maxInputChannels': 1,
        }
        self.mock_pa_instance.get_device_info_by_index.return_value = {
            'index': 0,
            'name': 'default_mic',
            'maxInputChannels': 1,
        }
        self.microphone = Microphone(self.input_settings)

    async def test_get_audio_stream(self):
        mock_stream = MagicMock()
        self.mock_pa_instance.open.return_value = mock_stream
        shutdown_event = asyncio.Event()

        # Simulate some data in the queue
        await self.microphone._input_queue.put(b'audio_chunk')

        # Start the generator as a task so we can stop it
        generator = self.microphone.get_audio_stream(shutdown_event)

        # Consume one item
        item = await generator.__anext__()
        self.assertEqual(item, b'audio_chunk')

        # Shutdown
        shutdown_event.set()
        # Put another item to unblock the queue.get() if needed
        await self.microphone._input_queue.put(b'stop')

        with self.assertRaises(StopAsyncIteration):
            await generator.__anext__()

        mock_stream.start_stream.assert_called_once()

    async def test_get_audio_stream_cancel(self):
        mock_stream = MagicMock()
        self.mock_pa_instance.open.return_value = mock_stream
        shutdown_event = asyncio.Event()

        generator = self.microphone.get_audio_stream(shutdown_event)

        # Run the generator in a task
        async def run_gen():
            async for _ in generator:
                pass

        task = asyncio.create_task(run_gen())

        # Let it start
        await asyncio.sleep(0.01)

        # Cancel it
        task.cancel()

        # Should not raise CancelledError
        await task
        self.assertTrue(mock_stream.start_stream.called)

    def test_stop_audio_stream(self):
        mock_stream = MagicMock()
        self.microphone._audio_stream = mock_stream

        self.microphone.stop_audio_stream()

        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        self.mock_pa_instance.terminate.assert_called_once()

    def test_stop_audio_stream_without_stream(self):
        self.microphone._audio_stream = None
        self.microphone.stop_audio_stream()
        self.mock_pa_instance.terminate.assert_called_once()

    def test_callback_success(self):
        self.microphone._loop = MagicMock()
        self.microphone._input_queue = asyncio.Queue(maxsize=1)

        res = self.microphone._callback(b'data')

        self.assertEqual(res, (None, pyaudio.paContinue))
        self.assertTrue(self.microphone._loop.call_soon_threadsafe.called)

    def test_callback_queue_full(self):
        self.microphone._loop = MagicMock()
        self.microphone._input_queue = MagicMock()
        self.microphone._input_queue.full.return_value = True

        res = self.microphone._callback(b'data')

        self.assertEqual(res, (None, pyaudio.paContinue))
        self.assertFalse(self.microphone._loop.call_soon_threadsafe.called)

    def test_callback_no_loop(self):
        self.microphone._loop = None

        res = self.microphone._callback(b'data')

        self.assertEqual(res, (None, pyaudio.paContinue))

    def test_get_input_device_fallback(self):
        self.mock_pa_instance.get_device_info_by_index.side_effect = Exception('Not found')

        device = self.microphone._get_input_device(99)

        self.assertEqual(device['name'], 'default_mic')

    def test_list_input_devices(self):
        self.mock_pa_instance.get_device_count.return_value = 1
        self.mock_pa_instance.get_device_info_by_index.return_value = {
            'index': 0,
            'name': 'mic1',
            'maxInputChannels': 1,
            'hostApi': 0,
        }

        devices = Microphone.list_input_devices()

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['name'], 'mic1')

    def test_list_input_devices_filter_no_input(self):
        self.mock_pa_instance.get_device_count.return_value = 1
        self.mock_pa_instance.get_device_info_by_index.return_value = {
            'index': 0,
            'name': 'output_only',
            'maxInputChannels': 0,
            'hostApi': 0,
        }

        devices = Microphone.list_input_devices()

        self.assertEqual(len(devices), 0)
