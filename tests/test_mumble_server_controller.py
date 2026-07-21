import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from controllers.mumble_server_controller import MumbleServerController, _ServerStartWorker


class TestMumbleServerController(unittest.TestCase):
    def setUp(self):
        self.install_dir = Path('/tmp/mumble-install')
        self.controller = MumbleServerController(self.install_dir)

        # Mock signals to verify emissions without needing a QApplication event loop
        self.controller.server_started = MagicMock()
        self.controller.server_stopped = MagicMock()
        self.controller.server_error = MagicMock()
        self.controller.status_changed = MagicMock()
        self.controller.channels_synced = MagicMock()
        self.controller.channels_sync_error = MagicMock()

    def test_is_running_false_when_no_process(self):
        self.assertFalse(self.controller.is_running())

    def test_is_running_true_when_process_alive(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        self.controller._process = mock_process

        self.assertTrue(self.controller.is_running())

    def test_is_running_false_when_process_exited(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = 0
        self.controller._process = mock_process

        self.assertFalse(self.controller.is_running())

    def test_start_emits_server_started_when_already_running(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        self.controller._process = mock_process

        self.controller.start('pw')

        self.controller.server_started.emit.assert_called_once()

    @patch('controllers.mumble_server_controller.Path.exists', return_value=False)
    def test_start_emits_error_when_binary_missing(self, _mock_exists):
        self.controller.start('pw')

        self.controller.server_error.emit.assert_called_once()
        self.assertIn('binary not found', self.controller.server_error.emit.call_args[0][0])

    def test_stop_does_nothing_when_not_running(self):
        self.controller.stop()

        self.controller.server_stopped.emit.assert_not_called()

    def test_stop_terminates_running_process(self):
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        self.controller._process = mock_process

        self.controller.stop()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        self.controller.server_stopped.emit.assert_called_once()
        self.assertIsNone(self.controller._process)

    def test_stop_disconnects_channel_manager(self):
        mock_manager = MagicMock()
        self.controller._channel_manager = mock_manager

        self.controller.stop()

        mock_manager.disconnect.assert_called_once()
        self.assertIsNone(self.controller._channel_manager)

    def test_sync_channels_emits_error_when_not_running(self):
        self.controller.sync_channels({'de', 'en'})

        self.controller.channels_sync_error.emit.assert_called_once_with('Mumble server is not running.')

    @patch('controllers.mumble_server_controller.threading.Thread')
    def test_sync_channels_starts_thread_when_running(self, mock_thread):
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        self.controller._process = mock_process
        self.controller._superuser_password = 'pw'

        self.controller.sync_channels({'de'})

        mock_thread.assert_called_once()
        self.assertTrue(mock_thread.return_value.start.called)

    def test_run_channel_manager_task_emits_error_without_password(self):
        on_error = MagicMock()

        self.controller._run_channel_manager_task('Task', action=lambda m: None, on_error=on_error)

        on_error.assert_called_once()

    def test_ensure_ini_creates_file_with_expected_content(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            install_dir = Path(tmp)
            ini_path = MumbleServerController._ensure_ini(install_dir)

            self.assertTrue(ini_path.exists())
            content = ini_path.read_text(encoding='utf-8')
            self.assertIn('port=64738', content)
            self.assertIn('database=', content)

    def test_ensure_ini_does_not_overwrite_existing_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            install_dir = Path(tmp)
            ini_path = install_dir / 'murmur.ini'
            ini_path.write_text('custom content', encoding='utf-8')

            result_path = MumbleServerController._ensure_ini(install_dir)

            self.assertEqual(ini_path.read_text(encoding='utf-8'), 'custom content')
            self.assertEqual(result_path, ini_path)


class TestServerStartWorker(unittest.TestCase):
    def setUp(self):
        self.worker = _ServerStartWorker(Path('/bin/murmurd'), Path('/tmp/murmur.ini'), 'pw', first_init=False)
        self.worker.started = MagicMock()
        self.worker.error = MagicMock()

    def test_use_new_opts_true_for_new_version(self):
        self.assertTrue(_ServerStartWorker._use_new_opts((1, 6, 0)))
        self.assertTrue(_ServerStartWorker._use_new_opts((2, 0, 0)))

    def test_use_new_opts_false_for_old_version_or_unknown(self):
        self.assertFalse(_ServerStartWorker._use_new_opts((1, 3, 0)))
        self.assertFalse(_ServerStartWorker._use_new_opts(None))

    @patch('controllers.mumble_server_controller.subprocess.run')
    def test_detect_murmur_version_parses_output(self, mock_run):
        mock_run.return_value = MagicMock(stdout='Murmur 1.4.230 (v1.4.230)\n', stderr='')

        version = _ServerStartWorker._detect_murmur_version('murmurd')

        self.assertEqual(version, (1, 4, 230))

    @patch('controllers.mumble_server_controller.subprocess.run')
    def test_detect_murmur_version_returns_none_when_unparseable(self, mock_run):
        mock_run.return_value = MagicMock(stdout='', stderr='')

        version = _ServerStartWorker._detect_murmur_version('murmurd')

        self.assertIsNone(version)

    def test_port_open_false_when_connection_fails(self):
        self.assertFalse(_ServerStartWorker._port_open(1))  # port 1 unlikely open/reserved
