import os
import sys

if sys.platform == 'win32':
    # Add vcpkg bin directory to DLL search path if VCPKG_PATH is set
    vcpkg_path = os.environ.get('VCPKG_PATH')
    if vcpkg_path:
        vcpkg_bin = os.path.join(vcpkg_path, 'installed', 'x64-windows', 'bin')
        if os.path.exists(vcpkg_bin):
            os.add_dll_directory(vcpkg_bin)
    
    # Also add current directory as a fallback
    try:
        os.add_dll_directory(os.getcwd())
    except Exception:
        pass
