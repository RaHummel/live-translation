import ctypes as real_ctypes
import unittest
from unittest.mock import MagicMock, patch

from utils import windows_firewall
from utils.windows_firewall import add_firewall_rules_elevated, firewall_rules_exist


def _mock_ctypes() -> MagicMock:
    """A MagicMock standing in for the `ctypes` module, keeping `sizeof`/`byref` real
    (they work fine on any OS) while stubbing out the Windows-only `windll` bits."""
    mock = MagicMock()
    mock.sizeof = real_ctypes.sizeof
    mock.byref = real_ctypes.byref
    return mock


class TestFirewallRulesExist(unittest.TestCase):
    @patch('utils.windows_firewall.sys.platform', 'darwin')
    def test_returns_false_on_non_windows(self):
        self.assertFalse(firewall_rules_exist(64738))

    @patch('utils.windows_firewall.subprocess.run')
    @patch('utils.windows_firewall.sys.platform', 'win32')
    def test_returns_true_when_both_rules_found(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout='Rule Name: LiveTranslation Mumble TCP 64738\n----\n Rule Name: LiveTranslation Mumble UDP 64738'
        )
        self.assertTrue(firewall_rules_exist(64738))
        self.assertEqual(mock_run.call_count, 2)

    @patch('utils.windows_firewall.subprocess.run')
    @patch('utils.windows_firewall.sys.platform', 'win32')
    def test_returns_false_when_rule_missing(self, mock_run):
        mock_run.return_value = MagicMock(stdout='No rules match the specified criteria.\n')
        self.assertFalse(firewall_rules_exist(64738))

    @patch('utils.windows_firewall.subprocess.run', side_effect=OSError('netsh missing'))
    @patch('utils.windows_firewall.sys.platform', 'win32')
    def test_returns_false_on_query_error(self, _mock_run):
        self.assertFalse(firewall_rules_exist(64738))


class TestAddFirewallRulesElevated(unittest.TestCase):
    @patch('utils.windows_firewall.sys.platform', 'darwin')
    def test_returns_false_on_non_windows(self):
        success, error = add_firewall_rules_elevated(64738)
        self.assertFalse(success)
        self.assertIn('Windows', error)

    @patch('utils.windows_firewall.sys.platform', 'win32')
    def test_returns_false_when_uac_denied(self):
        with patch.object(windows_firewall, 'ctypes', _mock_ctypes()) as mock_ctypes:
            mock_ctypes.windll.shell32.ShellExecuteExW.return_value = False
            mock_ctypes.GetLastError.return_value = 1223

            success, error = add_firewall_rules_elevated(64738)

            self.assertFalse(success)
            self.assertIn('denied', error)

    @patch('utils.windows_firewall.sys.platform', 'win32')
    def test_returns_true_on_success(self):
        with patch.object(windows_firewall, 'ctypes', _mock_ctypes()) as mock_ctypes:

            def fake_shell_execute(execute_info_ref):
                execute_info_ref._obj.hProcess = 12345  # fake non-null process handle
                return True

            def fake_get_exit_code(_handle, exit_code_ref):
                exit_code_ref._obj.value = 0

            mock_ctypes.windll.shell32.ShellExecuteExW.side_effect = fake_shell_execute
            mock_ctypes.windll.kernel32.GetExitCodeProcess.side_effect = fake_get_exit_code

            success, error = add_firewall_rules_elevated(64738)

            self.assertTrue(success)
            self.assertEqual(error, '')
            mock_ctypes.windll.kernel32.WaitForSingleObject.assert_called_once()
            mock_ctypes.windll.kernel32.CloseHandle.assert_called_once()

    @patch('utils.windows_firewall.sys.platform', 'win32')
    def test_returns_false_when_netsh_exits_with_error(self):
        with patch.object(windows_firewall, 'ctypes', _mock_ctypes()) as mock_ctypes:

            def fake_shell_execute(execute_info_ref):
                execute_info_ref._obj.hProcess = 12345
                return True

            def fake_get_exit_code(_handle, exit_code_ref):
                exit_code_ref._obj.value = 1

            mock_ctypes.windll.shell32.ShellExecuteExW.side_effect = fake_shell_execute
            mock_ctypes.windll.kernel32.GetExitCodeProcess.side_effect = fake_get_exit_code

            success, error = add_firewall_rules_elevated(64738)

            self.assertFalse(success)
            self.assertIn('error code', error)

    @patch('utils.windows_firewall.sys.platform', 'win32')
    def test_returns_false_when_process_handle_missing(self):
        with patch.object(windows_firewall, 'ctypes', _mock_ctypes()) as mock_ctypes:
            # hProcess stays 0 (falsy) — ShellExecuteExW "succeeded" but gave no handle back.
            mock_ctypes.windll.shell32.ShellExecuteExW.return_value = True

            success, error = add_firewall_rules_elevated(64738)

            self.assertFalse(success)
            self.assertIn('monitor', error)
