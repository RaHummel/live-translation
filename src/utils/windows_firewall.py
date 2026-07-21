import ctypes
import logging
import subprocess
import sys
from ctypes import wintypes

LOGGER = logging.getLogger(__name__)

_RULE_NAME_TCP = 'LiveTranslation Mumble TCP {port}'
_RULE_NAME_UDP = 'LiveTranslation Mumble UDP {port}'

# ShellExecuteExW / SHELLEXECUTEINFOW constants
_SEE_MASK_NOCLOSEPROCESS = 0x00000040
_SEE_MASK_NO_CONSOLE = 0x00008000
_SW_HIDE = 0
_INFINITE = 0xFFFFFFFF


class _SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('fMask', ctypes.c_ulong),
        ('hwnd', wintypes.HWND),
        ('lpVerb', wintypes.LPCWSTR),
        ('lpFile', wintypes.LPCWSTR),
        ('lpParameters', wintypes.LPCWSTR),
        ('lpDirectory', wintypes.LPCWSTR),
        ('nShow', ctypes.c_int),
        ('hInstApp', wintypes.HINSTANCE),
        ('lpIDList', ctypes.c_void_p),
        ('lpClass', wintypes.LPCWSTR),
        ('hKeyClass', wintypes.HKEY),
        ('dwHotKey', wintypes.DWORD),
        ('hIcon', wintypes.HANDLE),
        ('hProcess', wintypes.HANDLE),
    ]


def firewall_rules_exist(port: int) -> bool:
    """Return True if both the TCP and UDP inbound rules for *port* already exist.

    Runs `netsh advfirewall firewall show rule`, which does not require
    administrator privileges.
    """
    if sys.platform != 'win32':
        return False

    return _rule_exists(_RULE_NAME_TCP.format(port=port)) and _rule_exists(_RULE_NAME_UDP.format(port=port))


def _rule_exists(rule_name: str) -> bool:
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={rule_name}'],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        return rule_name in result.stdout
    except Exception as e:
        LOGGER.warning('Failed to query firewall rule "%s": %s', rule_name, e)
        return False


def add_firewall_rules_elevated(port: int) -> tuple[bool, str]:
    """Add inbound TCP+UDP firewall rules for *port*, prompting for admin rights.

    Launches a single elevated `cmd.exe` (triggers the Windows UAC dialog)
    that runs both `netsh advfirewall firewall add rule` commands, then
    waits for it to finish.

    Returns:
        (success, error_message). error_message is empty on success.
    """
    if sys.platform != 'win32':
        return False, 'Firewall rules are only supported on Windows.'

    tcp_name = _RULE_NAME_TCP.format(port=port)
    udp_name = _RULE_NAME_UDP.format(port=port)
    command = (
        f'netsh advfirewall firewall add rule name="{tcp_name}" dir=in action=allow protocol=TCP localport={port} '
        f'&& netsh advfirewall firewall add rule name="{udp_name}" dir=in action=allow protocol=UDP localport={port}'
    )
    parameters = f'/c {command}'

    execute_info = _SHELLEXECUTEINFOW()
    execute_info.cbSize = ctypes.sizeof(_SHELLEXECUTEINFOW)
    execute_info.fMask = _SEE_MASK_NOCLOSEPROCESS | _SEE_MASK_NO_CONSOLE
    execute_info.hwnd = None
    execute_info.lpVerb = 'runas'
    execute_info.lpFile = 'cmd.exe'
    execute_info.lpParameters = parameters
    execute_info.lpDirectory = None
    execute_info.nShow = _SW_HIDE
    execute_info.hInstApp = None

    shell32 = ctypes.windll.shell32  # type: ignore[attr-defined]
    if not shell32.ShellExecuteExW(ctypes.byref(execute_info)):  # type: ignore[attr-defined]
        error_code = ctypes.GetLastError()
        LOGGER.error('ShellExecuteExW failed (elevation likely rejected): error=%d', error_code)
        if error_code == 1223:  # ERROR_CANCELLED — user clicked "No" on the UAC prompt
            return False, 'Administrator privileges were denied.'
        return False, f'Could not add firewall rules (error code {error_code}).'

    process_handle = execute_info.hProcess
    if not process_handle:
        return False, 'Could not monitor the firewall process.'

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    try:
        kernel32.WaitForSingleObject(process_handle, _INFINITE)  # type: ignore[attr-defined]
        exit_code = wintypes.DWORD()
        kernel32.GetExitCodeProcess(process_handle, ctypes.byref(exit_code))  # type: ignore[attr-defined]
    finally:
        kernel32.CloseHandle(process_handle)  # type: ignore[attr-defined]

    if exit_code.value != 0:
        return False, f'netsh exited with error code {exit_code.value}.'

    LOGGER.info('Firewall rules for port %d added successfully.', port)
    return True, ''
