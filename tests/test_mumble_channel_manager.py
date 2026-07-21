import unittest
from unittest.mock import MagicMock, patch

from pymumble_py3.constants import PYMUMBLE_CONN_STATE_CONNECTED, PYMUMBLE_CONN_STATE_NOT_CONNECTED

from controllers.mumble_channel_manager import MumbleChannelManager


class TestMumbleChannelManager(unittest.TestCase):
    def setUp(self):
        self.manager = MumbleChannelManager(host='localhost', port=64738, password='secret')

    @patch('controllers.mumble_channel_manager.ensure_cert')
    @patch('controllers.mumble_channel_manager.Mumble')
    def test_connect_success(self, mock_mumble_cls, mock_ensure_cert):
        mock_ensure_cert.return_value = ('cert.pem', 'key.pem')
        mock_mumble = MagicMock()
        mock_mumble.connected = PYMUMBLE_CONN_STATE_CONNECTED
        mock_mumble_cls.return_value = mock_mumble

        result = self.manager.connect()

        self.assertTrue(result)
        mock_mumble.start.assert_called_once()
        mock_mumble.is_ready.assert_called_once()

    @patch('controllers.mumble_channel_manager.ensure_cert')
    @patch('controllers.mumble_channel_manager.Mumble')
    def test_connect_failure_not_connected(self, mock_mumble_cls, mock_ensure_cert):
        mock_ensure_cert.return_value = ('cert.pem', 'key.pem')
        mock_mumble = MagicMock()
        mock_mumble.connected = PYMUMBLE_CONN_STATE_NOT_CONNECTED
        mock_mumble_cls.return_value = mock_mumble

        result = self.manager.connect()

        self.assertFalse(result)

    @patch('controllers.mumble_channel_manager.ensure_cert')
    @patch('controllers.mumble_channel_manager.Mumble')
    def test_connect_handles_exception(self, mock_mumble_cls, mock_ensure_cert):
        mock_ensure_cert.side_effect = RuntimeError('boom')

        result = self.manager.connect()

        self.assertFalse(result)

    def test_disconnect_without_connection_does_not_raise(self):
        self.manager.disconnect()  # should be a no-op, no exception

    def test_disconnect_stops_and_clears_mumble(self):
        mock_mumble = MagicMock()
        self.manager._mumble = mock_mumble

        self.manager.disconnect()

        mock_mumble.stop.assert_called_once()
        self.assertIsNone(self.manager._mumble)

    def test_sync_channels_skips_when_not_connected(self):
        self.manager.sync_channels({'en', 'de'})  # no connection -> no-op, no exception

    def test_remove_all_channels_skips_when_not_connected(self):
        self.manager.remove_all_channels()  # no connection -> no-op, no exception

    def test_sync_channels_creates_and_removes(self):
        mock_mumble = MagicMock()
        mock_mumble.connected = PYMUMBLE_CONN_STATE_CONNECTED
        root_channel = {'name': 'root'}
        mock_mumble.channels.__getitem__.return_value = root_channel
        mock_mumble.channels.get_childs.return_value = [
            {'name': 'German', 'channel_id': 1},
            {'name': 'Obsolete', 'channel_id': 2},
        ]
        self.manager._mumble = mock_mumble

        with patch.object(self.manager, '_wait_for_channel', return_value=True):
            self.manager.sync_channels({'de'})

        mock_mumble.channels.remove_channel.assert_called_once_with(2)
        mock_mumble.channels.new_channel.assert_not_called()

    def test_remove_all_channels_removes_every_root_child(self):
        mock_mumble = MagicMock()
        mock_mumble.connected = PYMUMBLE_CONN_STATE_CONNECTED
        root_channel = {'name': 'root'}
        mock_mumble.channels.__getitem__.return_value = root_channel
        mock_mumble.channels.get_childs.return_value = [
            {'name': 'German', 'channel_id': 1},
            {'name': 'English', 'channel_id': 2},
        ]
        self.manager._mumble = mock_mumble

        self.manager.remove_all_channels()

        self.assertEqual(mock_mumble.channels.remove_channel.call_count, 2)

    def test_find_channel_returns_none_without_connection(self):
        self.assertIsNone(self.manager._find_channel('German'))

    def test_find_channel_returns_none_on_exception(self):
        mock_mumble = MagicMock()
        mock_mumble.channels.find_by_name.side_effect = Exception('unknown channel')
        self.manager._mumble = mock_mumble

        self.assertIsNone(self.manager._find_channel('German'))

    def test_existing_root_channels_empty_without_connection(self):
        self.assertEqual(self.manager._existing_root_channels(), {})

    def test_apply_root_acl_sends_update_command(self):
        mock_mumble = MagicMock()
        root_channel = MagicMock()
        mock_mumble.channels.__getitem__.return_value = root_channel
        self.manager._mumble = mock_mumble

        with patch('controllers.mumble_channel_manager.time.sleep'):
            self.manager._apply_root_acl()

        root_channel.request_acl.assert_called_once()
        mock_mumble.execute_command.assert_called_once()

    def test_apply_root_acl_warns_without_connection(self):
        self.manager._apply_root_acl()  # no mumble -> logs warning, no exception
