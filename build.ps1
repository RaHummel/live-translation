
$operation = $args[0]
$ZIP_FILE = "translation-service.zip"

Write-Host "Executing script with command: $operation"

function Lock-Dependencies {
    Write-Host "Locking dependencies..."
    pipenv run pipenv lock
}

function Install-Dependencies {
    Write-Host "Installing dependencies..."
    pipenv sync --dev
    pipenv graph
}

function Start-Shell {
    Write-Host "Starting Pipenv shell..."
    pipenv shell
}

function Bundle-Project {
    Write-Host "Bundling project..."

    # Create necessary directories if they don't exist
    $buildLibsPath = "build/libs"
    $buildDistributionPath = "build/distribution"

    if (-not (Test-Path $buildLibsPath)) {
        New-Item -ItemType Directory -Path $buildLibsPath | Out-Null
    }
    if (-not (Test-Path $buildDistributionPath)) {
        New-Item -ItemType Directory -Path $buildDistributionPath | Out-Null
    }

    # Generate the requirements.txt file
    pipenv run pipenv requirements > requirements.txt

    # Install dependencies into the build/libs directory
    pipenv run pip install -r requirements.txt -t $buildLibsPath

    # Recursively copy directories to the target directory
    Copy-Item -Recurse -Force "lib/mumble/pymumble_py3" "$buildLibsPath"
    Copy-Item -Recurse -Force "lib/py-opuslib/opuslib" "$buildLibsPath"

    # Zip the contents of build/libs and store it in build/distribution
    $libsZipPath = Join-Path -Path $buildDistributionPath -ChildPath $ZIP_FILE
    Compress-Archive -Path "$buildLibsPath/*" -DestinationPath $libsZipPath -Force

    # Zip the contents of src and add it to build/distribution
    $srcPath = "src/*"
    Compress-Archive -Path $srcPath -Update -DestinationPath $libsZipPath

    # Zip the contents of res and add it to build/distribution
    $resPath = "res"
    Compress-Archive -Path $resPath -Update -DestinationPath $libsZipPath

    Write-Host "Project has been successfully bundled and saved to $libsZipPath."
}


switch ($operation) {
    "lock" {
        Lock-Dependencies
    }
    "install" {
        Install-Dependencies
    }
    "shell" {
        Start-Shell
    }
    "bundle" {
        Bundle-Project
    }
    default {
        Write-Error "Invalid command. Use one of the following: lock, install, shell, bundle."
    }
}
