import logging
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from constants import MUMBLE_DEFAULT_PORT
from controllers.mumble_channel_manager import MumbleChannelManager
from utils.mumble_paths import find_murmur_binary, resolve_murmur_dir

LOGGER = logging.getLogger(__name__)

_STARTUP_TIMEOUT = 10  # seconds to wait for port to become available

# Murmur >= 1.6 changed argument style
_NEW_OPTS_MIN_VERSION = (1, 6)

_VERSION_RE = re.compile(r'(\d+)\.(\d+)\.(\d+)')


class _ServerStartWorker(QObject):
    """Runs in a QThread: starts Mumble Server and waits until the port is reachable."""

    started = Signal()
    error = Signal(str)

    def __init__(self, binary_path: Path, ini_path: Path, password: str, first_init: bool):
        super().__init__()
        self._binary_path = binary_path
        self._ini_path = ini_path
        self._password = password
        self._first_init = first_init
        self.process: subprocess.Popen | None = None

    def run(self):
        try:
            binary = str(self._binary_path)
            ini_path = str(self._ini_path)

            version = self._detect_murmur_version(binary)
            new_opts = self._use_new_opts(version)
            ini_flag = '--ini' if new_opts else '-ini'
            supw_flag = '--set-su-pw' if new_opts else '-supw'
            fg_flag = '--foreground' if new_opts else '-fg'
            LOGGER.info(
                'Detected Murmur Server version: %s (using %s CLI options).',
                '.'.join(map(str, version)) if version else 'unknown',
                'new' if new_opts else 'legacy',
            )

            # Step 1: first_init → supw is one-shot, sets password in DB and exits
            if self._first_init:
                LOGGER.info('Setting Mumble Server superuser password (%s).', supw_flag)
                result = subprocess.run(
                    [binary, ini_flag, ini_path, supw_flag, self._password],
                    timeout=15,
                )
                if result.returncode not in (0, 1):
                    raise RuntimeError(f'{supw_flag} exited with unexpected returncode={result.returncode}.')
                LOGGER.info('Superuser password set successfully.')

            # Step 2: start the actual server process
            args = [binary, ini_flag, ini_path]
            if sys.platform == 'darwin':
                args.append(fg_flag)  # foreground mode required on macOS, otherwise daemonizes

            LOGGER.info('Starting Mumble Server: %s', args)
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Poll until port reachable or timeout
            deadline = time.monotonic() + _STARTUP_TIMEOUT
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError(f'Mumble Server exited unexpectedly (returncode={self.process.returncode}).')
                if self._port_open(MUMBLE_DEFAULT_PORT):
                    LOGGER.info('Mumble Server is ready on port %d.', MUMBLE_DEFAULT_PORT)
                    self.started.emit()
                    return
                time.sleep(0.3)

            raise RuntimeError(f'Mumble Server did not become ready within {_STARTUP_TIMEOUT}s.')

        except Exception as e:
            LOGGER.error('Failed to start Mumble Server: %s', e, exc_info=True)
            self.error.emit(str(e))

    # TODO Should be removed in later version
    @staticmethod
    def _detect_murmur_version(binary: str) -> tuple[int, int, int] | None:
        """Try to determine the Murmur Server version by invoking it with a version flag.

        Tries both the legacy `-version` and the new `--version` flag, since we don't
        yet know which style the binary understands. Returns None if the version
        could not be determined (caller should then fall back to legacy short options).
        """
        for flag in ('-version', '--version'):
            try:
                result = subprocess.run(
                    [binary, flag],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                output = f'{result.stdout}\n{result.stderr}'
                match = _VERSION_RE.search(output)
                if match:
                    major, minor, patch = (int(part) for part in match.groups())
                    return major, minor, patch
            except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                LOGGER.debug('Version detection via %s failed: %s', flag, e)

        LOGGER.warning('Could not determine Murmur Server version, falling back to legacy CLI options.')
        return None

    @staticmethod
    def _use_new_opts(version: tuple[int, int, int] | None) -> bool:
        return version is not None and version[:2] >= _NEW_OPTS_MIN_VERSION

    @staticmethod
    def _port_open(port: int) -> bool:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except OSError:
            return False


class MumbleServerController(QObject):
    """Manages the lifecycle of a local Mumble Server process.

    Signals:
        server_started (): Emitted when Mumble Server is ready to accept connections.
        server_stopped (): Emitted when Mumble Server has been stopped.
        server_error (str): Emitted when starting Mumble Server fails.
        status_changed (str): Human-readable status update.
    """

    server_started = Signal()
    server_stopped = Signal()
    server_error = Signal(str)
    status_changed = Signal(str)
    channels_synced = Signal()
    channels_sync_error = Signal(str)

    def __init__(self, install_dir: Path, parent=None):
        super().__init__(parent)
        self._install_dir = install_dir
        self._process: subprocess.Popen | None = None
        self._start_thread: QThread | None = None
        self._start_worker: _ServerStartWorker | None = None
        self._channel_manager: MumbleChannelManager | None = None
        self._superuser_password: str | None = None

    def start(self, password: str, first_init: bool = False):
        """Start Mumble Server asynchronously.

        Args:
            password: The superuser password (used only when first_init=True).
            first_init: True → pass --supw to set the password in Mumble Server's DB.
        """
        self._superuser_password = password
        if self.is_running():
            LOGGER.debug('Mumble Server already running, skipping start.')
            self.server_started.emit()
            return

        binary_dir = resolve_murmur_dir(self._install_dir)
        binary = find_murmur_binary(binary_dir)
        if binary is None:
            msg = f'Mumble Server binary not found in {self._install_dir} or default install location.'
            LOGGER.error(msg)
            self.server_error.emit(msg)
            return

        ini_path = self._ensure_ini(self._install_dir)

        self.status_changed.emit('Starting Mumble server…')

        self._start_thread = QThread(self)
        self._start_worker = _ServerStartWorker(binary, ini_path, password, first_init)
        self._start_worker.moveToThread(self._start_thread)

        thread = self._start_thread
        worker = self._start_worker

        thread.started.connect(worker.run)
        worker.started.connect(self._on_worker_started)
        worker.error.connect(self._on_worker_error)
        worker.started.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)

        thread.start()

    def stop(self):
        """Stop the running Mumble Server process."""
        if self._channel_manager is not None:
            self._channel_manager.disconnect()
            self._channel_manager = None

        if self._process is None or self._process.poll() is not None:
            LOGGER.debug('Mumble Server not running, nothing to stop.')
            return

        LOGGER.info('Stopping Mumble Server…')
        self.status_changed.emit('Stopping Mumble server…')
        try:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                LOGGER.warning('Mumble Server did not terminate within 5s, killing.')
                self._process.kill()
        except Exception as e:
            LOGGER.error('Error stopping Mumble Server: %s', e)
        finally:
            self._process = None
            self.status_changed.emit('Mumble server stopped.')
            LOGGER.info('Mumble Server stopped.')
            self.server_stopped.emit()

    def is_running(self) -> bool:
        """Returns True if the Mumble Server process is alive."""
        return self._process is not None and self._process.poll() is None

    def sync_channels(self, target_languages: set[str]) -> None:
        """Create/remove language channels on the embedded server to match *target_languages*.

        Runs asynchronously (connect + sync happen entirely in a background
        thread); emits `channels_synced` on completion or `channels_sync_error`
        if the sync could not be performed.
        """
        if not self.is_running():
            LOGGER.debug('sync_channels: server not running, skipping.')
            self.channels_sync_error.emit('Mumble server is not running.')
            return

        self._run_channel_manager_task(
            'MumbleChannelSync',
            action=lambda manager: manager.sync_channels(target_languages),
            track_for_cancellation=True,
            on_success=self.channels_synced.emit,
            on_error=self.channels_sync_error.emit,
        )

    def _on_worker_started(self):
        # Grab the Popen handle from the worker before thread cleans up
        if self._start_worker is not None:
            self._process = self._start_worker.process
        self.status_changed.emit('Mumble server running.')
        self.server_started.emit()
        self._clear_root_channels()

    def _clear_root_channels(self) -> None:
        """Wipe any leftover root-level language channels right when the
        Mumble server (re-)starts, before anyone calls `sync_channels()`.

        Uses its own short-lived SuperUser connection (connect → wipe →
        disconnect), independent of the one `sync_channels()` opens later.
        """
        self._run_channel_manager_task(
            'MumbleClearChannels',
            action=lambda manager: manager.remove_all_channels(),
        )

    def _run_channel_manager_task(
        self,
        task_name: str,
        action,
        *,
        track_for_cancellation: bool = False,
        on_success=None,
        on_error=None,
    ) -> None:
        """Run *action(manager)* against a fresh SuperUser channel-manager connection.

        Connects, runs the action and disconnects again — all in a background
        daemon thread, so no part of it ever blocks the UI thread. The SuperUser
        connection is only needed to set up channels/ACLs (AI translators
        authenticate via access token, see `MumbleChannelManager`), so it's
        always torn down again immediately after *action* completes.

        If *track_for_cancellation* is True, the manager is exposed via
        `self._channel_manager` while connected, so `stop()` can disconnect it
        early if the server is stopped while the task is still running.
        """
        password = self._superuser_password
        if password is None:
            msg = f'{task_name}: no superuser password stored.'
            LOGGER.warning(msg)
            if on_error is not None:
                on_error(msg)
            return

        def _run():
            manager = MumbleChannelManager(host='127.0.0.1', port=MUMBLE_DEFAULT_PORT, password=password)
            try:
                if not manager.connect():
                    raise RuntimeError(f'{task_name}: could not connect channel manager.')
                if track_for_cancellation:
                    self._channel_manager = manager
                action(manager)
                if on_success is not None:
                    on_success()
            except Exception as e:
                LOGGER.error('%s: error: %s', task_name, e, exc_info=True)
                if on_error is not None:
                    on_error(str(e))
            finally:
                if track_for_cancellation and self._channel_manager is manager:
                    self._channel_manager = None
                manager.disconnect()

        threading.Thread(target=_run, daemon=True, name=task_name).start()

    def _on_worker_error(self, msg: str):
        self._process = None
        self.status_changed.emit(f'Mumble server error: {msg}')
        self.server_error.emit(msg)

    @staticmethod
    def _ensure_ini(install_dir: Path) -> Path:
        """Create murmur.ini with explicit database path if it doesn't exist."""
        ini_path = install_dir / 'murmur.ini'
        db_path = install_dir / 'murmur.sqlite'
        log_path = install_dir / 'murmur.log'

        LOGGER.info('Creating murmur.ini at %s', ini_path)
        if not ini_path.exists():
            welcometext = (
                '<br />Welcome to <b>Live Translation</b>!<br />'
                'Join a language channel to listen to the live translation.<br />'
            )
            ini_path.write_text(
                f'database={db_path}\n'
                f'logfile={log_path}\n'
                f'port={MUMBLE_DEFAULT_PORT}\n'
                'allowping=true\n'
                'registerName=Live Translation\n'
                f'welcometext={welcometext}\n',
                encoding='utf-8',
            )
            LOGGER.info('Created murmur.ini at %s', ini_path)

        return ini_path
