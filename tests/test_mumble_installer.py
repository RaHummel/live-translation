import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sound_outputs.mumble_installer import MumbleInstaller


class TestMumbleInstallerAssetMatching(unittest.TestCase):
    @patch('sound_outputs.mumble_installer.sys.platform', 'darwin')
    def test_asset_matches_macos(self):
        installer = MumbleInstaller(Path('/tmp/install'))
        self.assertTrue(installer._asset_matches('mumble_server-1.5.0.x64.macos'))
        self.assertFalse(installer._asset_matches('mumble_server-1.5.0.x64.exe'))

    @patch('sound_outputs.mumble_installer.sys.platform', 'win32')
    def test_asset_matches_windows(self):
        installer = MumbleInstaller(Path('/tmp/install'))
        self.assertTrue(installer._asset_matches('mumble_server-1.5.0.x64.exe'))
        self.assertFalse(installer._asset_matches('mumble_server-1.5.0.x64.macos'))

    @patch('sound_outputs.mumble_installer.sys.platform', 'linux')
    def test_asset_matches_unsupported_platform(self):
        installer = MumbleInstaller(Path('/tmp/install'))
        self.assertFalse(installer._asset_matches('mumble_server-1.5.0.x64.macos'))


class TestMumbleInstallerRun(unittest.TestCase):
    def setUp(self):
        self.install_dir = Path('/tmp/mumble-install-test')
        self.installer = MumbleInstaller(self.install_dir)
        self.installer.progress = MagicMock()
        self.installer.finished = MagicMock()

    @patch('sound_outputs.mumble_installer.Path.mkdir')
    @patch('sound_outputs.mumble_installer.urllib.request.urlopen')
    def test_run_emits_failure_when_no_matching_asset(self, mock_urlopen, _mock_mkdir):
        release = {'assets': [{'name': 'mumble-1.5.0.x64.exe', 'browser_download_url': 'http://x', 'size': 10}]}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(release).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with patch('sound_outputs.mumble_installer.sys.platform', 'darwin'):
            self.installer.run()

        self.installer.finished.emit.assert_called_once()
        success, message = self.installer.finished.emit.call_args[0]
        self.assertFalse(success)
        self.assertIn('No matching asset', message)

    @patch('sound_outputs.mumble_installer.Path.mkdir')
    @patch('sound_outputs.mumble_installer.urllib.request.urlopen')
    def test_run_emits_failure_when_request_fails(self, mock_urlopen, _mock_mkdir):
        mock_urlopen.side_effect = OSError('network down')

        self.installer.run()

        self.installer.finished.emit.assert_called_once_with(False, 'network down')

    @patch('sound_outputs.mumble_installer.os.chmod')
    @patch('sound_outputs.mumble_installer.shutil.copy2')
    @patch('sound_outputs.mumble_installer.Path.mkdir')
    @patch('sound_outputs.mumble_installer.urllib.request.urlretrieve')
    @patch('sound_outputs.mumble_installer.urllib.request.urlopen')
    def test_run_success_on_macos_extracts_binary(
        self, mock_urlopen, mock_urlretrieve, _mock_mkdir, mock_copy2, mock_chmod
    ):
        release = {
            'assets': [{'name': 'mumble_server-1.5.0.x64.macos', 'browser_download_url': 'http://x', 'size': 10}]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(release).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with (
            patch('sound_outputs.mumble_installer.sys.platform', 'darwin'),
            patch('sound_outputs.mumble_installer.Path.exists', return_value=True),
            patch('sound_outputs.mumble_installer.Path.unlink'),
        ):
            self.installer.run()

        mock_copy2.assert_called_once()
        mock_chmod.assert_called_once()
        self.installer.finished.emit.assert_called_once_with(True, '')
        self.installer.progress.emit.assert_any_call(100)
