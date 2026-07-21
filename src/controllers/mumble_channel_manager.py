import contextlib
import logging
import threading
import time
from pathlib import Path

from pymumble_py3 import Mumble, messages
from pymumble_py3.constants import PYMUMBLE_CONN_STATE_CONNECTED

from constants import MUMBLE_TRANSLATOR_TOKEN
from utils.language_names import display_name
from utils.mumble_certs import CERTS_DIR, ensure_cert

LOGGER = logging.getLogger(__name__)

# Mumble ACL permission bits (from Mumble source: src/Permissions.h)
# None=0x0, Write=0x1, Traverse=0x2, Enter=0x4, Speak=0x8, MuteDeafen=0x10,
# Move=0x20, MakeChannel=0x40, LinkChannel=0x80, Whisper=0x100, TextMessage=0x200,
# MakeTempChannel=0x400, Listen=0x1000, Kick=0x10000, Ban=0x20000, Register= 0x40000,
# SelfRegister=0x80000,
_PERM_SPEAK = 0x8
_PERM_WHISPER = 0x100


class MumbleChannelManager:
    """Manages language channels directly under the Mumble root channel.

    Each language channel gets an ACL that:
        @all                                → deny SPEAK + WHISPER (listen-only for everyone)
        group "#<MUMBLE_TRANSLATOR_TOKEN>"  → grant SPEAK

    The SPEAK grant uses a Mumble *access token* group: group names prefixed
    with ``#`` match any connecting client that presents that token string
    (see ``pymumble.Mumble(tokens=[...])``, used by ``MumbleClient``). This
    requires **no client certificate and no server-side registration** — any
    AI translator session that connects with the right token immediately has
    SPEAK in every language channel, regardless of its username or how many
    sessions connect simultaneously. This sidesteps the pitfalls of
    certificate/registration-based group membership (identity collisions when
    sessions would share a certificate).
    """

    def __init__(self, host: str, port: int, password: str, cert_dir: Path | None = None):
        self._host = host
        self._port = port
        self._password = password
        self._cert_dir = cert_dir or CERTS_DIR
        self._mumble: Mumble | None = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Open a SuperUser connection.  Returns True on success."""
        try:
            certfile, keyfile = ensure_cert(
                self._cert_dir / 'admin_cert.pem',
                self._cert_dir / 'admin_key.pem',
                'LiveTranslation-ChannelAdmin',
            )

            self._mumble = Mumble(
                host=self._host,
                port=self._port,
                user='SuperUser',
                password=self._password,
                certfile=certfile,
                keyfile=keyfile,
                reconnect=False,
            )
            self._mumble.start()
            self._mumble.is_ready()

            if self._mumble.connected != PYMUMBLE_CONN_STATE_CONNECTED:
                LOGGER.error('MumbleChannelManager: SuperUser connection failed.')
                return False

            LOGGER.info('MumbleChannelManager: connected as SuperUser.')
            self._apply_root_acl()
            return True
        except Exception as e:
            LOGGER.error('MumbleChannelManager: connect error: %s', e, exc_info=True)
            return False

    def disconnect(self) -> None:
        """Close the SuperUser connection."""
        if self._mumble is not None:
            with contextlib.suppress(Exception):
                self._mumble.stop()
            self._mumble = None

    @property
    def _is_connected(self) -> bool:
        return self._mumble is not None and self._mumble.connected == PYMUMBLE_CONN_STATE_CONNECTED

    def sync_channels(self, target_languages: set[str]) -> None:
        """Create/remove root-level language channels to match *target_languages*."""
        if not self._is_connected:
            LOGGER.warning('MumbleChannelManager: not connected, skipping sync.')
            return

        with self._lock:
            self._sync(target_languages)

    def remove_all_channels(self) -> None:
        """Remove every existing direct child channel of the root channel.

        Intended to be called once when the Mumble server itself starts (see
        ``MumbleServerController``), so it always begins with a clean slate —
        any leftover language channels from a previous run are gone before
        `sync_channels()` later creates the currently configured ones.
        Requires an active connection (see `connect()`).
        """
        if not self._is_connected:
            LOGGER.warning('MumbleChannelManager: not connected, skipping channel removal.')
            return

        with self._lock:
            for name, channel_id in self._existing_root_channels().items():
                self._remove_channel(name, channel_id)

    def _find_channel(self, name: str):
        """Return the channel dict for *name*, or None if not found (incl. UnknownChannelError)."""
        try:
            if self._mumble is None:
                return None
            return self._mumble.channels.find_by_name(name)
        except Exception:
            return None

    def _existing_root_channels(self) -> dict[str, int]:
        """Return {name: channel_id} for all direct children of the root channel."""
        result: dict[str, int] = {}
        if self._mumble is None:
            return result
        try:
            # get_childs requires a channel dict, NOT a bare integer
            root = self._mumble.channels[0]
            for ch in self._mumble.channels.get_childs(root):
                result[ch['name']] = ch['channel_id']
        except Exception as e:
            LOGGER.warning('MumbleChannelManager: could not list root channels: %s', e)
        return result

    def _remove_channel(self, name: str, channel_id: int) -> None:
        """Remove a single channel by id, logging (but not raising) on failure."""
        if self._mumble is None:
            return
        try:
            self._mumble.channels.remove_channel(channel_id)
            LOGGER.debug('MumbleChannelManager: removed channel "%s".', name)
        except Exception as e:
            LOGGER.warning('MumbleChannelManager: could not remove channel "%s": %s', name, e)

    def _sync(self, target_languages: set[str]) -> None:
        if self._mumble is None:
            return
        target_names = {display_name(lang) for lang in target_languages}

        existing = self._existing_root_channels()
        existing_names = set(existing.keys())

        to_create = target_names - existing_names
        to_remove = existing_names - target_names

        for name in to_remove:
            self._remove_channel(name, existing[name])

        for name in to_create:
            try:
                self._mumble.channels.new_channel(0, name, temporary=False)
                self._wait_for_channel(name)
                LOGGER.debug('MumbleChannelManager: created channel "%s".', name)
            except Exception as e:
                LOGGER.warning('MumbleChannelManager: could not create "%s": %s', name, e, exc_info=True)

    def _wait_for_channel(self, name: str, timeout: float = 3.0) -> bool:
        """Poll until the channel appears in the channels dict or timeout expires."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._find_channel(name) is not None:
                return True
            time.sleep(0.1)
        LOGGER.warning('MumbleChannelManager: timeout waiting for channel "%s".', name)
        return False

    def _apply_root_acl(self) -> None:
        """Set ACL once on the root channel (id=0).

        All language sub-channels inherit this ACL automatically:
            @all                                → deny SPEAK + WHISPER (listen-only for everyone)
            group "#<MUMBLE_TRANSLATOR_TOKEN>"  → grant SPEAK

        Critical notes
        --------------
        * ``inherited`` **must** be explicitly ``False`` for each entry we own.
          The Mumble proto2 default for ``inherited`` is ``True``, and pymumble's
          ``treat_command`` only appends an entry when ``not chan_acl.inherited``.
          A ``None`` value is treated as "not set" → falls back to proto default
          ``True`` → the entry is silently dropped.
        * Query the current ACL first (``request_acl``) so the server accepts our
          update without rejecting it as stale.
        * The ``#`` prefix on the group name makes this a Mumble *access token*
          group — no ``chan_group``/registration bookkeeping needed, any client
          presenting the token via ``tokens=[...]`` at connect time matches it.
        """
        try:
            if self._mumble is None:
                LOGGER.warning('MumbleChannelManager: ACL error - mumble not initialized.')
                return
            LOGGER.debug('Setting ACL on root channel (id=0).')
            root = self._mumble.channels[0]
            root.request_acl()
            time.sleep(0.5)  # Give server time to respond

            chan_acl = [
                # Deny SPEAK + WHISPER for everyone
                {
                    'apply_here': True,
                    'apply_subs': True,
                    'inherited': False,  # MUST be False — see docstring
                    'user_id': None,
                    'group': 'all',
                    'grant': None,
                    'deny': _PERM_SPEAK | _PERM_WHISPER,
                },
                # Grant SPEAK to anyone presenting the AI translator access token
                {
                    'apply_here': True,
                    'apply_subs': True,
                    'inherited': False,  # MUST be False — see docstring
                    'user_id': None,
                    'group': f'#{MUMBLE_TRANSLATOR_TOKEN}',
                    'grant': _PERM_SPEAK,
                    'deny': None,
                },
            ]

            cmd = messages.UpdateACL(
                channel_id=0,
                inherit_acls=True,
                chan_group=[],
                chan_acl=chan_acl,
            )
            self._mumble.execute_command(cmd)
            LOGGER.debug('MumbleChannelManager: ACL applied to root channel (id=0).')
        except Exception as e:
            LOGGER.warning('MumbleChannelManager: ACL error for root channel: %s', e, exc_info=True)
