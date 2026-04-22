$ErrorActionPreference = "Stop"

$python = $env:PYTHON
if ([string]::IsNullOrWhiteSpace($python)) {
    $python = "python"
}

& $python -m PyInstaller file-compressor.spec --noconfirm
