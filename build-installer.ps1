# Build script for creating Windows installer (.exe) for Live Translation
# This script uses PyInstaller to bundle the application and NSIS to create the installer

param(
    [switch]$SkipNSIS = $false
)

# Extract version from pyproject.toml
$pyprojectContent = Get-Content "pyproject.toml" -Raw
if ($pyprojectContent -match 'version = "([^"]+)"') {
    $VERSION = $matches[1]
} else {
    Write-Error "Could not find version in pyproject.toml"
    exit 1
}

$APP_NAME = "LiveTranslation"
$EXE_NAME = "${APP_NAME}.exe"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Live Translation - Windows Build Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if running on Windows
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "This script requires PowerShell 5.0 or higher"
    exit 1
}

# Check for Python and uv
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed. Please install it first."
    Write-Host "Download from: https://github.com/astral-sh/uv" -ForegroundColor Yellow
    exit 1
}

Write-Host "All prerequisites satisfied." -ForegroundColor Green
Write-Host ""

# Ensure vcpkg and native audio libraries (PortAudio, Opus) are available for building
Write-Host "Ensuring native audio libraries (PortAudio, Opus) via vcpkg..." -ForegroundColor Yellow

# Default vcpkg path (can be overridden by user environment)
$defaultVcpkg = "C:\tools\vcpkg"
if (-not [string]::IsNullOrEmpty($env:VCPKG_PATH)) {
    $vcpkgPath = $env:VCPKG_PATH
} else {
    $vcpkgPath = $defaultVcpkg
}

if (-not (Test-Path $vcpkgPath)) {
    Write-Host "vcpkg not found at $vcpkgPath - cloning to $defaultVcpkg..." -ForegroundColor Yellow
    git clone https://github.com/microsoft/vcpkg.git $defaultVcpkg
    if (-not (Test-Path "$defaultVcpkg/bootstrap-vcpkg.bat")) {
        Write-Warning "Failed to clone vcpkg. Please install vcpkg manually and re-run this script."
    } else {
        Write-Host "Found bootstrap script at: $defaultVcpkg/bootstrap-vcpkg.bat" -ForegroundColor Green
        Push-Location $defaultVcpkg
        & .\bootstrap-vcpkg.bat
        Pop-Location
        $vcpkgPath = $defaultVcpkg
    }
}

# Export VCPKG_PATH for this process so subsequent commands use it
$env:VCPKG_PATH = $vcpkgPath
Write-Host "Using vcpkg at: $vcpkgPath" -ForegroundColor Green

# Install PortAudio and Opus via vcpkg (x64)
if (Test-Path "$vcpkgPath\vcpkg.exe") {
    Write-Host "Installing portaudio and opus via vcpkg... (this may take a while)" -ForegroundColor Yellow
    & "$vcpkgPath\vcpkg.exe" install portaudio:x64-windows
    & "$vcpkgPath\vcpkg.exe" install opus:x64-windows
} else {
    Write-Warning "vcpkg.exe not found at $vcpkgPath. Skipping native library install - PyAudio/Opus build may fail."
}


# Install PyInstaller if not already installed
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
try {
    uv pip install pyinstaller --system 2>$null
} catch {
    uv pip install pyinstaller
}

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Run PyInstaller
Write-Host "Running PyInstaller..." -ForegroundColor Yellow

# Export APP_NAME into the process environment so the spec file can read it via os.environ
$env:APP_NAME = $APP_NAME
uv run pyinstaller live-translation.spec --clean --noconfirm

if (-not (Test-Path "dist/$APP_NAME/$EXE_NAME")) {
    Write-Error "PyInstaller build failed. Executable not found at dist/$APP_NAME/$EXE_NAME"
    exit 1
}

Write-Host "Application bundled successfully at dist/$APP_NAME/$EXE_NAME" -ForegroundColor Green
Write-Host ""

# Copy native DLLs (PortAudio, Opus) from vcpkg into dist/$APP_NAME/_internal so they are available at runtime
$vcpkgBin = "$env:VCPKG_PATH\installed\x64-windows\bin"
if (Test-Path $vcpkgBin) {
    Write-Host "Copying native DLLs from $vcpkgBin into dist/$APP_NAME/_internal/..." -ForegroundColor Yellow
    $dlls = Get-ChildItem -Path $vcpkgBin -Filter *.dll -File -ErrorAction SilentlyContinue
    if ($dlls.Count -gt 0) {
        foreach ($dll in $dlls) {
            try {
                Copy-Item $dll.FullName -Destination "dist/$APP_NAME/_internal/" -Force
            } catch {
                Write-Warning "Failed to copy $($dll.Name): $_"
            }
        }
        Write-Host "Copied $($dlls.Count) DLL(s) into dist/$APP_NAME/_internal/" -ForegroundColor Green
    } else {
        Write-Warning "No DLLs found in $vcpkgBin to copy. If you rely on PortAudio/Opus, ensure vcpkg installed them."
    }
} else {
    Write-Warning "vcpkg bin path not found at $vcpkgBin. Native runtime DLLs wont be copied into the bundle."
}

# Create NSIS installer
if (-not $SkipNSIS) {
    Write-Host "Creating Windows installer with NSIS..." -ForegroundColor Yellow
    
    # Check for NSIS
    $nsisPath = $null
    $possiblePaths = @(
        "C:\Program Files (x86)\NSIS\makensis.exe",
        "C:\Program Files\NSIS\makensis.exe",
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
        "${env:ProgramFiles}\NSIS\makensis.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $nsisPath = $path
            break
        }
    }
    
    if (-not $nsisPath) {
        Write-Warning "NSIS not found. Skipping installer creation."
        Write-Host "To create an installer, install NSIS from: https://nsis.sourceforge.io/" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Standalone application is available at: dist/$APP_NAME/$EXE_NAME" -ForegroundColor Green
    } else {
        # Create installers directory
        New-Item -ItemType Directory -Force -Path "dist/installers" | Out-Null

        # Run NSIS to create installer with version and app name parameters
        & $nsisPath "/DAPP_NAME=$APP_NAME" "/DAPP_VERSION=$VERSION" "installer\windows\installer.nsi"

        if (Test-Path "dist/installers/$EXE_NAME") {
            Write-Host "Installer created successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Installer location: dist/installers/$EXE_NAME" -ForegroundColor Cyan
        } else {
            Write-Warning "Installer creation failed."
        }
    }
} else {
    Write-Host "Skipping NSIS installer creation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application bundle: dist/$EXE_NAME" -ForegroundColor Green

if (-not $SkipNSIS -and (Test-Path "dist/installers/$EXE_NAME")) {
    Write-Host "Installer: dist/installers/$EXE_NAME" -ForegroundColor Green
}

Write-Host ""
Write-Host "To test the application:" -ForegroundColor Yellow
Write-Host " 1. Navigate to: dist/$APP_NAME/$EXE_NAME" -ForegroundColor White
Write-Host " 2. Run: ./${EXE_NAME}" -ForegroundColor White
Write-Host ""