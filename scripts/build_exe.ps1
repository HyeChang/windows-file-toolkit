param(
    [string]$Python = $env:PYTHON
)

$ErrorActionPreference = "Stop"

$python = $Python
if ([string]::IsNullOrWhiteSpace($python)) {
    $python = "python"
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$jpegtranPath = Join-Path $projectRoot "tools/jpegtran/jpegtran.exe"
$jpegtranDllPath = Join-Path $projectRoot "tools/jpegtran/jpeg62.dll"
if ((Test-Path $jpegtranPath) -and (Test-Path $jpegtranDllPath)) {
    Write-Host "JPEG rotation bundle: including tools/jpegtran/jpegtran.exe"
}
else {
    Write-Host "JPEG rotation bundle: tools/jpegtran/jpegtran.exe or tools/jpegtran/jpeg62.dll not found; JPEG rotation will require PATH or be skipped."
}

& $python -m PyInstaller file-compressor.spec --noconfirm
