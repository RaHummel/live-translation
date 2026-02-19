"""
PyInstaller hook for PyAudio to ensure PortAudio library is included.
"""

import sys

binaries = []
datas = []

if sys.platform == 'darwin':
    # Mac: include PortAudio from Homebrew
    binaries = [
        ('/opt/homebrew/lib/libportaudio.2.dylib', '.'),
        ('/opt/homebrew/lib/libportaudio.dylib', '.'),
    ]
elif sys.platform == 'win32':
    # Windows: PyAudio wheel includes PortAudio
    pass
