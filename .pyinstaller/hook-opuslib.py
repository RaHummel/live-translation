"""
PyInstaller hook for opuslib workspace dependency.
This ensures opuslib and the native Opus library are properly bundled.
"""

import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all opuslib submodules
hiddenimports = collect_submodules('opuslib')

# Collect any data files
datas = collect_data_files('opuslib', include_py_files=True)

# Platform-specific library handling
binaries = []
if sys.platform == 'darwin':
    # Mac: include Opus library
    binaries = [
        ('/usr/local/lib/libopus.0.dylib', '.'),
        ('/usr/local/lib/libopus.dylib', '.'),
    ]
elif sys.platform == 'win32':
    # Windows: Opus library should be in system PATH
    # or can be bundled if available
    pass
