# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Live Translation application.
This file configures how PyInstaller bundles the application for distribution.
"""

import sys
import os
import tomllib
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Add local library paths to sys.path so hooks can find them
base_path = os.path.abspath('.')
sys.path.insert(0, os.path.join(base_path, 'lib', 'py-opuslib', 'src'))
sys.path.insert(0, os.path.join(base_path, 'lib', 'mumble', 'src'))

block_cipher = None

# Determine if we're building on Mac
IS_MAC = sys.platform == 'darwin'
IS_WINDOWS = sys.platform == 'win32'

# Application metadata
APP_NAME = os.environ.get('APP_NAME', 'Live Translation')

# Read version from pyproject.toml
base_path = os.path.abspath('.')
with open(os.path.join(base_path, 'pyproject.toml'), 'rb') as f:
    pyproject = tomllib.load(f)
    APP_VERSION = pyproject['project']['version']

print(f"Building {APP_NAME} version {APP_VERSION}")


# Collect all PySide6 modules
pyside6_modules = collect_submodules('PySide6')

# Hidden imports - modules that PyInstaller might miss
hidden_imports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'boto3',
    'botocore',
    'amazon_transcribe',
    'opuslib',
    'pymumble_py3',
    'pymumble_py3.soundqueue',
    'pymumble_py3.commands',
    'pymumble_py3.constants',
    'pyaudio',
    'google.protobuf',
    'google.protobuf.descriptor',
    'google.protobuf.message',
    # AWS SDK modules
    'botocore.vendored',
    'botocore.vendored.requests',
] + pyside6_modules

# Data files to include
datas = [
    ('src/styles', 'styles'),  # Include themes and icons
]

# Binary files (shared libraries)
binaries = []

# Platform-specific configurations
if IS_MAC:
    # On Mac, include system libraries
    binaries += [
        ('/opt/homebrew/lib/libportaudio.dylib', '.'),
        ('/usr/local/lib/libopus.dylib', '.'),
    ]
elif IS_WINDOWS:
    # On Windows, PyAudio includes PortAudio
    # Opus library needs to be in PATH or bundled separately
    pass

a = Analysis(
    ['src/main.py'],
    pathex=[
        base_path,
        os.path.join(base_path, 'src'),
        os.path.join(base_path, 'lib', 'mumble', 'src'),
        os.path.join(base_path, 'lib', 'py-opuslib'),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=['.pyinstaller'],  # Custom hooks directory
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'mypy',
        'ruff',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=f'{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='img/live-translation-app.icns' if not IS_WINDOWS else 'img/live-translation-app.ico',  # Icon for app
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# Mac app bundle (only on Mac)
if IS_MAC:
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon='img/live-translation-app.icns',
        bundle_identifier=f'com.rahummel.{APP_NAME}',
        version=APP_VERSION,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleVersion': APP_VERSION,
            'CFBundleShortVersionString': APP_VERSION,
            'NSMicrophoneUsageDescription': 'This app requires microphone access for live audio translation.',
        },
    )