import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from utils.mumble_paths import get_windows_mumble_dir
from utils.windows_firewall import add_firewall_rules_elevated

LOGGER = logging.getLogger(__name__)

GITHUB_API_URL = 'https://api.github.com/repos/mumble-voip/mumble/releases/latest'


class MumbleInstaller(QObject):
    """Downloads and installs the Mumble server binary from GitHub Releases.

    Signals:
        progress (int): Download progress 0–100.
        finished (bool, str): True + empty string on success, False + error message on failure.
    """

    progress = Signal(int)
    finished = Signal(bool, str)

    def __init__(self, install_dir: Path, parent=None):
        super().__init__(parent)
        self._install_dir = install_dir
        # Actual directory the binary ended up in. Normally equal to `_install_dir`,
        # but on Windows the installer may ignore our custom path and fall back to
        # its own default location (see `_install_windows`). Read this after
        # `finished` has been emitted to find out where the server really lives.
        self.resolved_install_dir: Path = install_dir

    def run(self):
        """Fetch, download, and install the Mumble server. Run in a worker thread."""
        tmp_path: Path | None = None
        try:
            self._install_dir.mkdir(parents=True, exist_ok=True)

            # 1. Fetch latest release metadata
            LOGGER.info('Fetching latest Mumble release info from GitHub...')
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    'User-Agent': 'LiveTranslation-App',
                    'Accept': 'application/json',
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                release = json.loads(resp.read().decode())

            # 2. Find matching asset for this platform
            assets = release.get('assets', [])
            asset = next((a for a in assets if self._asset_matches(a['name'])), None)

            if asset is None:
                available = [a['name'] for a in assets]
                raise RuntimeError(
                    f'No matching asset found for platform "{sys.platform}".\nAvailable assets: {available}'
                )

            download_url = asset['browser_download_url']
            asset_name = asset['name']
            total_size = asset.get('size', 0)
            LOGGER.info(f'Downloading {asset_name} ({total_size} bytes) from {download_url}')

            # 3. Download to temp file with progress reporting
            suffix = ''.join(Path(asset_name).suffixes) or '.bin'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp_path = Path(tmp.name)

            def reporthook(block_num: int, block_size: int, file_size: int):
                size = file_size if file_size > 0 else total_size
                if size > 0:
                    pct = int(min(block_num * block_size, size) * 100 / size)
                    self.progress.emit(min(pct, 99))

            urllib.request.urlretrieve(download_url, tmp_path, reporthook=reporthook)
            self.progress.emit(99)

            # 4. Extract / install
            assert tmp_path is not None
            if sys.platform == 'darwin':
                self._extract_macos(tmp_path)
            elif sys.platform == 'win32':
                self._install_windows(tmp_path)
            else:
                raise RuntimeError(f'Unsupported platform: {sys.platform}')

            self.progress.emit(100)
            LOGGER.info('Mumble server installed successfully.')
            self.finished.emit(True, '')

        except Exception as e:
            LOGGER.error(f'Mumble install failed: {e}', exc_info=True)
            self.finished.emit(False, str(e))
        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def _extract_macos(self, archive_path: Path):
        """Copy murmurd binary to install dir and set executable bit."""
        target = self._install_dir / 'murmurd'
        shutil.copy2(archive_path, target)
        os.chmod(target, 0o755)
        LOGGER.info(f'murmurd installed to {target}')

    def _install_windows(self, exe_path: Path):
        """Install the Mumble server via the silent NSIS installer.

        The official Mumble Windows installer does not honor a custom
        target-directory switch — it always installs to its own default
        location.

        Raises:
            RuntimeError: If the installer fails or the binary cannot be
                found afterward, so `run()` doesn't mistakenly report success.
        """
        result = subprocess.run(
            [str(exe_path), '/S'],
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f'Mumble installer exited with returncode={result.returncode}.')

        found_dir = get_windows_mumble_dir()
        if found_dir is None:
            raise RuntimeError('Mumble Server binary not found in any default install location after installation.')

        self.resolved_install_dir = found_dir
        LOGGER.info(f'Mumble Server installed to default location {found_dir}.')

    @staticmethod
    def _asset_matches(name: str) -> bool:
        """Returns True if the asset name matches the current platform."""
        if not name.startswith('mumble_server'):
            return False
        if sys.platform == 'darwin':
            return name.endswith('.x64.macos')
        elif sys.platform == 'win32':
            return name.endswith('.x64.exe')
        return False


class FirewallRuleWorker(QObject):
    """Runs in a QThread: adds the Windows Firewall inbound rules for the Mumble port.

    Signals:
        finished (bool, str): True + empty string on success, False + error message on failure.
    """

    finished = Signal(bool, str)

    def __init__(self, port: int, parent=None):
        super().__init__(parent)
        self._port = port

    def run(self):
        """Add the firewall rules. Run in a worker thread (blocks until the elevated process exits)."""
        success, error_msg = add_firewall_rules_elevated(self._port)
        self.finished.emit(success, error_msg)
