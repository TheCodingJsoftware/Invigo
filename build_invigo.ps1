$ErrorActionPreference = "Stop"

# ================= CONFIG =================
$REPO_URL   = "https://github.com/TheCodingJsoftware/Invigo.git"
$PROJECT_DIR = "Invigo-Build"
$SPEC_FILE   = "Invigo.spec"
$UV          = "uv"
$ENV_FILE    = Join-Path $PROJECT_DIR ".env"

# ================= LOAD .env =================
if (-not (Test-Path $ENV_FILE)) {
    Write-Error ".env file not found at $ENV_FILE"
}

Get-Content $ENV_FILE |
    Where-Object { $_ -match "=" -and -not $_.StartsWith("#") } |
    ForEach-Object {
        $k, $v = $_ -split "=", 2
        Set-Variable -Name $k -Value $v -Scope Script
    }

$SOFTWARE_API_BASE = $SOFTWARE_API_BASE.Trim().Trim('"')

if (-not $SOFTWARE_API_BASE) {
    Write-Error "SOFTWARE_API_BASE not set in .env"
}

# ================= CLONE OR PULL =================
if (-not (Test-Path $PROJECT_DIR)) {
    Write-Host "Cloning repository..."
    git clone $REPO_URL $PROJECT_DIR
} else {
    Write-Host "Pulling latest changes..."
    Push-Location $PROJECT_DIR
    git pull
    Pop-Location
}

# ================= ENTER PROJECT DIR =================
Set-Location $PROJECT_DIR

# ================= ENSURE uv =================
Write-Host "Ensuring uv is installed..."
python -m pip install --upgrade pip | Out-Null

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    pip install uv
}

# ================= VENV =================
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    uv venv
}

Write-Host "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

# ================= DEPENDENCIES =================
if (Test-Path "pyproject.toml") {
    Write-Host "Installing dependencies from pyproject.toml..."
    uv pip install .
}
elseif (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..."
    uv pip install -r requirements.txt
}
else {
    throw "No pyproject.toml or requirements.txt found"
}

# ================= FETCH CURRENT VERSION =================
Write-Host "Fetching current version..."

$currentVersion = $null
try {
    $resp = Invoke-RestMethod "$SOFTWARE_API_BASE/version"
    $currentVersion = $resp.version
} catch {}

if ($currentVersion) {
    Write-Host "Current version: $currentVersion"
} else {
    Write-Host "No existing version found"
}

# ================= AUTO-INCREMENT VERSION =================
if (-not $currentVersion) {
    $nextVersion = "0.1.0"
} else {
    $p = $currentVersion.Split(".")
    $nextVersion = "{0}.{1}.{2}" -f $p[0], $p[1], ([int]$p[2] + 1)
}

$newVersion = Read-Host "Press ENTER to accept [$nextVersion] or type a different version"
if (-not $newVersion) {
    $newVersion = $nextVersion
}

$changelog = Read-Host "Enter release notes / changelog"

Write-Host "Using version: $newVersion"

# ================= BUILD =================
Write-Host "Building with PyInstaller..."
pyinstaller $SPEC_FILE

# ================= COPY RESOURCES =================
Write-Host "Copying resources..."

Copy-Item ui\themes dist\ui\themes -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ui\style  dist\ui\style  -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item icons     dist\icons     -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item sounds    dist\sounds    -Recurse -Force -ErrorAction SilentlyContinue

"LICENSE","README.md","CHANGELOG.md" | ForEach-Object {
    if (Test-Path $_) {
        Copy-Item $_ dist\ -Force
    }
}

# ================= ZIP =================
Write-Host "Zipping dist directory..."

$zipPath = "Invigo.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "dist\*" -DestinationPath $zipPath -Force

if (-not (Test-Path $zipPath)) {
    throw "ZIP creation failed"
}

# ================= UPLOAD =================
Write-Host "Uploading Invigo.zip..."

& curl.exe -X POST `
  "$SOFTWARE_API_BASE/upload?version=$newVersion&uploaded_by=jared&changelog=$([uri]::EscapeDataString($changelog))" `
  -F "file=@$zipPath"

Write-Host "Upload successful"

# ================= VERIFY =================
$verify = Invoke-RestMethod "$SOFTWARE_API_BASE/version"
Write-Host "Server reports version: $($verify.version)"

Write-Host "=== Build complete ==="
Pause
