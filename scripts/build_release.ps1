param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> ServerDeck release build" -ForegroundColor Cyan
Write-Host "    Root: $Root"

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "==> Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "==> Installing dependencies..." -ForegroundColor Yellow
& "venv\Scripts\python.exe" -m pip install --upgrade pip | Out-Null
& "venv\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-dev.txt

Write-Host "==> Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }

Write-Host "==> Building executable with PyInstaller..." -ForegroundColor Yellow
& "venv\Scripts\pyinstaller.exe" --noconfirm ServerDeck.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

$ExePath = Join-Path $Root "dist\ServerDeck\ServerDeck.exe"
if (-not (Test-Path $ExePath)) {
    throw "Expected executable was not created: $ExePath"
}

Write-Host "==> Executable ready: $ExePath" -ForegroundColor Green

if ($SkipInstaller) {
    Write-Host "==> Skipping installer (-SkipInstaller)." -ForegroundColor Yellow
    exit 0
}

$Iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Iscc) {
    Write-Host "==> Inno Setup not found. Install from:" -ForegroundColor Yellow
    Write-Host "    https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "    Then re-run: .\scripts\build_release.ps1" -ForegroundColor Yellow
    exit 0
}

Write-Host "==> Building installer with Inno Setup..." -ForegroundColor Yellow
& $Iscc "installer\ServerDeck.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup build failed." }

$SetupPath = Join-Path $Root "installer\output\ServerDeck-Setup-1.0.0.exe"
Write-Host "==> Installer ready: $SetupPath" -ForegroundColor Green
