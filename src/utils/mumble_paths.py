"""Helpers to locate the installed Mumble Server binary.

The official Windows Mumble installer's silent-install "/D=" custom
target-directory switch is not honored by every release — it always
installs to its own default location (Program Files\\Mumble\\server),
regardless of the path we pass. These helpers make sure the app can still
find (and start) the binary, and copy/create the murmur.ini next to it,
even when it ends up somewhere other than our managed app-config directory.
"""

import logging
import os
import sys
from pathlib import Path

from constants import MURMUR_BINARY

LOGGER = logging.getLogger(__name__)


def find_murmur_binary(directory: Path) -> Path | None:
    """Return the path to the Mumble server binary inside *directory*, if present."""
    candidate = directory / MURMUR_BINARY
    return candidate if candidate.exists() else None


def get_windows_mumble_dir() -> Path | None:
    """Return the first well-known default install location where the Mumble server is found.

    Returns None if no installation is found in any of the standard locations.
    """
    for env_var in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)'):
        base = os.environ.get(env_var)

        if base:
            server_dir = Path(base) / 'Mumble' / 'server'
            if find_murmur_binary(server_dir) is not None:
                LOGGER.info(f'Looking up default install location for {server_dir}')
                return server_dir
    return None


def resolve_murmur_dir(preferred_dir: Path) -> Path:
    """Return the directory that actually contains the Mumble server binary.

    On Windows, the installer always installs to its own default location
    (Program Files\\Mumble\\server) regardless of any custom path we
    request, so we look there directly. On other platforms we manage the
    binary ourselves at *preferred_dir*. Returns *preferred_dir* unchanged
    if nothing is found (caller is expected to handle the "not installed" case).
    """
    if sys.platform == 'win32':
        found_dir = get_windows_mumble_dir()
        if found_dir is not None:
            return found_dir
        return preferred_dir

    return preferred_dir
