# PyInstaller Build System - Troubleshooting Guide

This document provides troubleshooting tips for common issues when building installers.

## Common Issues

### Mac Build Issues

#### 1. "libportaudio.dylib not found"
**Solution:**
```sh
brew install portaudio
```

#### 2. "libopus.dylib not found"
**Solution:**
```sh
brew install opus
sudo mkdir -p /usr/local/lib
sudo cp $(brew --prefix opus)/lib/libopus.* /usr/local/lib/
```

#### 3. "create-dmg: command not found"
**Solution:**
```sh
brew install create-dmg
```

#### 4. "App can't be opened because it is from an unidentified developer"
This is expected for unsigned apps. To open:
1. Right-click the app
2. Select "Open"
3. Click "Open" in the dialog

**For distribution**, you should code-sign the app. See [Code Signing](#code-signing) below.

### Windows Build Issues

#### 1. "NSIS not found"
NSIS is optional. The script creates a standalone bundle at `dist/live-translation/` that can be zipped and distributed.

To create a proper installer:
1. Download NSIS from https://nsis.sourceforge.io/
2. Install to default location
3. Re-run the build script

#### 2. "PyInstaller failed: No module named 'PySide6'"
Make sure dependencies are installed:
```powershell
uv sync
```

#### 3. "ImportError: DLL load failed"
This usually means a required DLL is missing. Check that:
- PortAudio is properly installed
- Opus library is in system PATH

#### PortAudio / PyAudio build (Windows, `uv`)
If `uv sync` fails building `pyaudio` with a missing `portaudio.h` or similar errors, follow these steps:

1. Ensure `vcpkg` is installed and bootstrapped (example path: `C:\tools\vcpkg`):
```powershell
git clone https://github.com/microsoft/vcpkg.git C:\tools\vcpkg
cd C:\tools\vcpkg
.\bootstrap-vcpkg.bat
```

2. Set the `VCPKG_PATH` environment variable (system-wide requires Admin):
```powershell
# system-wide (Admin)
Start-Process powershell -Verb RunAs
# then in the elevated window:
setx VCPKG_PATH "C:\tools\vcpkg" -m

# OR for current user (no Admin)
setx VCPKG_PATH "C:\tools\vcpkg"
```

3. Install PortAudio via `vcpkg` for x64:
```powershell
cd C:\tools\vcpkg
.\vcpkg.exe install portaudio:x64-windows
.\vcpkg.exe list | Select-String portaudio
```

4. (Optional but effective) For the current terminal session add the vcpkg include/lib paths so native builds find `portaudio.h` immediately:
```powershell
$env:INCLUDE = "C:\tools\vcpkg\installed\x64-windows\include;$env:INCLUDE"
$env:LIB = "C:\tools\vcpkg\installed\x64-windows\lib;$env:LIB"
```

5. Re-run dependency sync / build in your project:
```powershell
# from project root
uv sync
```

Notes / troubleshooting:
- If `uv sync` still reports `portaudio.h` missing, verify `C:\tools\vcpkg\installed\x64-windows\include\portaudio.h` exists.
- If you cannot install `vcpkg` or prefer a quicker workaround, use a Python interpreter version with prebuilt wheels for `pyaudio` (commonly 3.11): create a virtualenv with that interpreter and select it in VS Code.
- In VS Code select the project interpreter created by `uv` (or your `.venv`) via Command Palette → "Python: Select Interpreter" → choose `./.venv/Scripts/python.exe` or the `uv`-installed Python executable path.

#### Opus library (Windows, `uv`)
If the app fails to start with an error like `Could not find Opus library`, follow these steps:

1. Install Opus via `vcpkg` for x64 (vcpkg should already be installed from PortAudio steps above):
```powershell
cd C:\tools\vcpkg
.\vcpkg.exe install opus:x64-windows
.\vcpkg.exe list | Select-String opus
```

2. Verify the Opus DLL is in the correct location:
```powershell
Test-Path C:\tools\vcpkg\installed\x64-windows\bin\opus.dll
```

3. For the current terminal session, add the vcpkg bin path to PATH (the build environment should have picked it up automatically, but runtime may need it):
```powershell
$env:PATH = 'C:\tools\vcpkg\installed\x64-windows\bin;' + $env:PATH
uv run python src/main.py
```

4. To make this permanent, add `C:\tools\vcpkg\installed\x64-windows\bin` to your system PATH (User or System environment variables) and restart your terminal/IDE or copy DLL to your .venv\Scripts path
```powershell
$dll = Get-ChildItem C:\tools\vcpkg\installed\x64-windows -Recurse -Include "opus*.dll","libopus*.dll" | Select-Object -First 1
Copy-Item $dll.FullName -Destination ".\.venv\Scripts\" -Force
```


Notes / troubleshooting:
- If you still get "Could not find Opus library" at runtime, verify that `C:\tools\vcpkg\installed\x64-windows\bin` is on your system `PATH`.
- If the app then fails with "DLL load failed", the Opus DLL may need additional dependencies; run `uv run python src/main.py -v` (verbose) to see which DLL is missing.

### Cross-Platform Issues

#### 1. "ModuleNotFoundError: No module named 'pymumble_py3'"
The workspace dependencies need to be in the Python path. Make sure:
- `lib/mumble/src` is in the pathex
- The hook file exists at `.pyinstaller/hook-pymumble_py3.py`

#### 2. "Unable to find config.json"
Check the spec file has the correct datas entry:
```python
datas = [
    ('src/config/config.json', 'config'),
]
```

#### 3. Build succeeds but app crashes on startup
Enable debug mode in the spec file:
```python
exe = EXE(
    ...
    console=True,  # Show console for debugging
    debug=True,    # Enable debug output
    ...
)
```

Run PyInstaller manually to see detailed errors:
```sh
pyinstaller live-translation.spec --clean --noconfirm --log-level DEBUG
```

## Code Signing

### Mac Code Signing

To distribute your app without security warnings:

1. **Join Apple Developer Program** ($99/year)

2. **Get a Developer ID certificate:**
   - Open Xcode
   - Preferences → Accounts → Manage Certificates
   - Create "Developer ID Application" certificate

3. **Sign the app:**
```sh
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/live-translation.app
```

4. **Notarize the app** (required for macOS 10.15+):
```sh
xcrun notarytool submit dist/installers/LiveTranslation-1.0.0-macOS.dmg \
    --apple-id "your-email@example.com" \
    --password "app-specific-password" \
    --team-id "TEAM_ID" \
    --wait
```

5. **Staple the notarization:**
```sh
xcrun stapler staple dist/installers/LiveTranslation-1.0.0-macOS.dmg
```

### Windows Code Signing

1. **Get a Code Signing Certificate** from a trusted CA (e.g., DigiCert, Sectigo)

2. **Sign the executable:**
```powershell
signtool sign /f "path\to\certificate.pfx" /p "password" /tr http://timestamp.digicert.com /td sha256 /fd sha256 "dist\live-translation\live-translation.exe"
```

3. **Sign the installer:**
```powershell
signtool sign /f "path\to\certificate.pfx" /p "password" /tr http://timestamp.digicert.com /td sha256 /fd sha256 "dist\installers\LiveTranslation-1.0.0-Windows-Setup.exe"
```

## Performance Optimization

### Reducing Bundle Size

1. **Exclude unnecessary packages** in the spec file:
```python
excludes=[
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'pytest',
    'mypy',
    'ruff',
],
```

2. **Use UPX compression** (already enabled):
```python
upx=True,
```

3. **Remove debug symbols:**
```python
strip=True,  # Remove debug symbols (currently False for debugging)
```

### Faster Builds

- Use `--noconfirm` to skip prompts
- Don't use `--clean` during development (only for release builds)
- Cache dependencies by not deleting `build/` between builds

## Architecture-Specific Builds

### Mac Universal Binary (Intel + Apple Silicon)

PyInstaller doesn't natively support universal binaries. To create one:

1. Build on Intel Mac: `./build-installer.sh`
2. Build on Apple Silicon Mac: `./build-installer.sh`
3. Use `lipo` to combine:
```sh
lipo -create -output live-translation \
    dist-intel/live-translation.app/Contents/MacOS/live-translation \
    dist-arm/live-translation.app/Contents/MacOS/live-translation
```

Or build for both architectures on Apple Silicon:
```sh
arch -x86_64 ./build-installer.sh  # Intel
arch -arm64 ./build-installer.sh   # ARM
```

## Getting Help

If you encounter issues not covered here:

1. Check PyInstaller documentation: https://pyinstaller.org/
2. Run with debug logging: `pyinstaller --log-level DEBUG live-translation.spec`
3. Check the PyInstaller GitHub issues: https://github.com/pyinstaller/pyinstaller/issues
