import unittest
from unittest.mock import MagicMock, patch

from botocore.response import StreamingBody

from config.model.config_models import MumbleSettings, OutputSettings, SpeakerSettings
from sound_outputs.speaker import Speaker


class TestSpeaker(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.output_settings = OutputSettings(
            output_method='speaker',
            output_sample_rate=16000,
            chunk_len=1024,
            speaker_settings=SpeakerSettings(output_device='default', output_device_index=0),
            mumble_settings=MumbleSettings(ip_address='localhost', port=64738, language_channel_mapping={}),
        )

        self.patcher = patch('pyaudio.PyAudio')
        self.mock_pa = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.mock_pa_instance = self.mock_pa.return_value

        self.mock_pa_instance.get_default_output_device_info.return_value = {
            'index': 0,
            'name': 'default_spk',
            'maxOutputChannels': 2,
        }
        self.mock_pa_instance.get_device_info_by_index.return_value = {
            'index': 0,
            'name': 'default_spk',
            'maxOutputChannels': 2,
        }
        self.speaker = Speaker(self.output_settings)

    def test_init_invalid_channels(self):
        self.mock_pa_instance.get_device_info_by_index.return_value = {
            'index': 0,
            'name': 'invalid_spk',
            'maxOutputChannels': 0,
        }
        self.mock_pa_instance.get_default_output_device_info.return_value = {
            'index': 0,
            'name': 'invalid_spk',
            'maxOutputChannels': 0,
        }

        with self.assertRaises(ValueError):
            Speaker(self.output_settings)

    async def test_play_success(self):
        mock_output_stream = MagicMock(spec=StreamingBody)
        # Read method returns empty bytes to stop the loop
        mock_output_stream.read.return_value = b''
        mock_stream = MagicMock()
        self.mock_pa_instance.open.return_value = mock_stream

        await self.speaker.play(mock_output_stream)

        self.assertTrue(mock_stream.start_stream.called)
        self.assertTrue(mock_stream.stop_stream.called)
        self.assertTrue(mock_stream.close.called)
        self.assertFalse(self.speaker._is_playing)

    async def test_play_already_playing(self):
        self.speaker._is_playing = True

        await self.speaker.play(MagicMock())

        self.assertFalse(self.mock_pa_instance.open.called)

    def test_stop_audio_stream(self):
        self.speaker._is_playing = True

        self.speaker.stop_audio_stream()

        self.assertFalse(self.speaker._is_playing)
        self.mock_pa_instance.terminate.assert_called_once()

    def test_play_blocking_reads_data(self):
        mock_stream = MagicMock()
        mock_output_stream = MagicMock(spec=StreamingBody)
        mock_output_stream.read.side_effect = [b'data1', b'data2', b'']
        self.speaker._is_playing = True

        self.speaker._play_blocking(mock_output_stream, mock_stream)

        self.assertEqual(mock_output_stream.read.call_count, 3)
        self.assertEqual(mock_stream.write.call_count, 2)

    def test_get_output_device_fallback(self):
        self.mock_pa_instance.get_device_info_by_index.side_effect = Exception('Not found')

        device = self.speaker._get_output_device(99)

        self.assertEqual(device['name'], 'default_spk')

    def test_list_output_devices(self):
        self.mock_pa_instance.get_device_count.return_value = 1
        self.mock_pa_instance.get_device_info_by_index.return_value = {
            'name': 'spk1',
            'index': 0,
            'maxOutputChannels': 2,
        }

        devices = Speaker.list_output_devices()

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['name'], 'spk1')
