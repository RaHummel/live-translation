#!/bin/bash
# Build script for creating Mac installer (.dmg) for Live Translation
# This script uses PyInstaller to bundle the application and create-dmg to create the installer

set -e  # Exit on error

APP_NAME="Live Translation"
APP_BUNDLE_NAME="Live Translation.app"

# Extract version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
DMG_NAME="LiveTranslation-${VERSION}.dmg"

echo "======================================"
echo "Live Translation - Mac Build Script"
echo "======================================"
echo ""

# Check if running on Mac
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script must be run on macOS"
    exit 1
fi

# Check for required tools
echo "Checking prerequisites..."

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew is not installed. Please install it from https://brew.sh"
    exit 1
fi

# Check for required dependencies
MISSING_DEPS=()
if ! brew list portaudio &> /dev/null; then
    MISSING_DEPS+=("portaudio")
fi
if ! brew list opus &> /dev/null; then
    MISSING_DEPS+=("opus")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo "Missing dependencies: ${MISSING_DEPS[@]}"
    echo "Installing missing dependencies..."
    brew install "${MISSING_DEPS[@]}"
fi

# Ensure Opus is in the correct location
echo "Ensuring Opus library is in /usr/local/lib..."
sudo mkdir -p /usr/local/lib
if [ -f "$(brew --prefix opus)/lib/libopus.dylib" ]; then
    sudo cp "$(brew --prefix opus)/lib/libopus."* /usr/local/lib/ 2>/dev/null || true
fi

# Check for Python and uv
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing via Homebrew..."
    brew install uv
fi

echo "All prerequisites satisfied."
echo ""

# Install PyInstaller if not already installed
echo "Installing PyInstaller..."
uv pip install pyinstaller --system 2>/dev/null || uv pip install pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Export APP_NAME for the spec to consume and run PyInstaller
export APP_NAME
echo "Running PyInstaller..."
uv run pyinstaller live-translation.spec --clean --noconfirm

# Check if build was successful
if [ ! -d "dist/${APP_BUNDLE_NAME}" ]; then
    echo "Error: PyInstaller build failed. App bundle not found at dist/${APP_BUNDLE_NAME}"
    exit 1
fi

echo "App bundle created successfully at dist/${APP_BUNDLE_NAME}"
echo ""

# Create DMG installer
echo "Creating DMG installer..."

# Check for create-dmg tool
if ! command -v create-dmg &> /dev/null; then
    echo "Installing create-dmg..."
    brew install create-dmg
fi

# Create installers directory
mkdir -p dist/installers

# Remove old DMG if exists
rm -f "dist/installers/${DMG_NAME}"

# Create DMG with create-dmg
# --volicon does not work currently 
create-dmg \
    --volname "${APP_NAME}" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "${APP_BUNDLE_NAME}" 175 120 \
    --hide-extension "${APP_BUNDLE_NAME}" \
    --app-drop-link 425 120 \
    --no-internet-enable \
    "dist/installers/${DMG_NAME}" \
    "dist/${APP_BUNDLE_NAME}"


echo ""
echo "======================================"
echo "Build completed successfully!"
echo "======================================"
echo ""
echo "Installer location: dist/installers/${DMG_NAME}"
echo ""
echo "To test the application:"
echo "  1. Mount the DMG: open dist/installers/${DMG_NAME}"
echo "  2. Drag the app to Applications"
echo "  3. Run from Applications folder"
echo ""
echo "Note: The app is not code-signed. Users may need to right-click"
echo "      and select 'Open' the first time to bypass Gatekeeper."
echo ""
