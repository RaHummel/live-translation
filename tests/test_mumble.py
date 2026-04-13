import unittest
from unittest.mock import MagicMock, patch

from botocore.response import StreamingBody
from pymumble_py3.constants import PYMUMBLE_CONN_STATE_CONNECTED, PYMUMBLE_CONN_STATE_NOT_CONNECTED

from config.model.config_models import MumbleSettings, OutputSettings
from sound_outputs.mumble import MumbleClient


class TestMumbleClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mumble_settings = MumbleSettings(
            ip_address='localhost', port=64738, language_channel_mapping={'de': 'Main/German', 'en': 'English'}
        )
        self.output_settings = OutputSettings(
            output_method='mumble',
            output_sample_rate=16000,
            chunk_len=1024,
            speaker_settings=None,
            mumble_settings=self.mumble_settings,
        )

        with patch('sound_outputs.mumble.Mumble'):
            self.client = MumbleClient(self.output_settings, 'de')
            self.mock_mumble = self.client._mumble

    def test_connect_success(self):
        self.mock_mumble.connected = PYMUMBLE_CONN_STATE_CONNECTED
        mock_channel = MagicMock()
        self.mock_mumble.channels.find_by_tree.return_value = mock_channel

        self.client.connect()

        self.mock_mumble.start.assert_called_once()
        self.mock_mumble.is_ready.assert_called_once()
        mock_channel.move_in.assert_called_once()

    def test_connect_failure(self):
        self.mock_mumble.connected = PYMUMBLE_CONN_STATE_NOT_CONNECTED

        with self.assertRaises(ConnectionError):
            self.client.connect()

        self.mock_mumble.stop.assert_called_once()

    async def test_play_success(self):
        mock_output = MagicMock(spec=StreamingBody)
        mock_output.read.side_effect = [b'data1', b'data2', b'']
        self.mock_mumble.sound_output = MagicMock()

        await self.client.play(mock_output)

        self.assertEqual(self.mock_mumble.sound_output.add_sound.call_count, 2)

    async def test_play_sound_output_not_init(self):
        mock_output = MagicMock(spec=StreamingBody)
        mock_output.read.side_effect = [b'data1', b'']
        self.mock_mumble.sound_output = None

        await self.client.play(mock_output)
        # Should not crash, just log warning

    def test_connect_with_single_channel(self):
        self.mock_mumble.connected = PYMUMBLE_CONN_STATE_CONNECTED
        self.client._channel_name = 'SingleChannel'
        mock_channel = MagicMock()
        self.mock_mumble.channels.find_by_name.return_value = mock_channel

        self.client.connect()

        mock_channel.move_in.assert_called_once()
        self.mock_mumble.channels.find_by_name.assert_called_with('SingleChannel')

    def test_connect_with_channel_tree(self):
        self.mock_mumble.connected = PYMUMBLE_CONN_STATE_CONNECTED
        self.client._channel_name = 'Main/Sub'
        mock_channel = MagicMock()
        self.mock_mumble.channels.find_by_tree.return_value = mock_channel

        self.client.connect()

        mock_channel.move_in.assert_called_once()
        self.mock_mumble.channels.find_by_tree.assert_called_with(['Main', 'Sub'])

    def test_connect_with_invalid_channel_path(self):
        self.mock_mumble.connected = PYMUMBLE_CONN_STATE_CONNECTED
        self.client._channel_name = 'Too/Deep/Path'

        with self.assertRaises(ValueError):
            self.client.connect()

    def test_stop_audio_stream(self):
        self.client.stop_audio_stream()

        self.mock_mumble.stop.assert_called_once()
