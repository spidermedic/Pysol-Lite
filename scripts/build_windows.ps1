# Build the Windows app: dist\PySol Lite\PySol Lite.exe
# Prerequisites: .venv with the packages from HANDOFF-WINDOWS.md.
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$py = '.\.venv\Scripts\python.exe'
$env:PYTHONPATH = (Get-Location).Path

# help pages (data\html is generated and git-ignored)
if (-not (Test-Path 'data\html')) {
    Push-Location html-src
    & ..\$py gen-html.py
    Pop-Location
    Copy-Item html-src\images html-src\html\images -Recurse
    Move-Item html-src\html data\html
}

& $py -m PyInstaller --noconfirm --clean pysol.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
Write-Host 'Built dist\PySol Lite\PySol Lite.exe'

# Installer (needs Inno Setup 6: winget install JRSoftware.InnoSetup)
$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    Write-Host 'Inno Setup 6 not found; skipping the installer.'
    return
}
$version = & $py -c "from pysollib.settings import VERSION; print(VERSION)"
& $iscc "/DAppVersion=$version" scripts\pysol-lite.iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }
Write-Host "Built dist\PySol-Lite-$version-Windows-setup.exe"
