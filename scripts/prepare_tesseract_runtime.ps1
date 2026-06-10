param(
    [string]$OutputDir = "",
    [string]$TempDir = "",
    [string]$InstallerUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $projectRoot "dist/tesseract-runtime"
}
if ([string]::IsNullOrWhiteSpace($TempDir)) {
    $TempDir = Join-Path $projectRoot ".test-output/ocr-download"
}

New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
if (Test-Path $OutputDir) {
    Remove-Item $OutputDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$installer = Join-Path $TempDir "tesseract-setup.exe"
Invoke-WebRequest -Uri $InstallerUrl -OutFile $installer

$arguments = @(
    "/VERYSILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART",
    "/DIR=$OutputDir"
)
$process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
if ($process.ExitCode -ne 0) {
    throw "Tesseract installer failed with exit code $($process.ExitCode)."
}

$tesseractExe = Join-Path $OutputDir "tesseract.exe"
if (-not (Test-Path $tesseractExe)) {
    $fallbackRoot = "D:\ocr"
    if (Test-Path (Join-Path $fallbackRoot "tesseract.exe")) {
        Copy-Item (Join-Path $fallbackRoot "*") $OutputDir -Recurse -Force
    }
}

$tessdata = Join-Path $OutputDir "tessdata"
New-Item -ItemType Directory -Force -Path $tessdata | Out-Null
Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_fast/raw/main/kor.traineddata" -OutFile (Join-Path $tessdata "kor.traineddata")
Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata" -OutFile (Join-Path $tessdata "eng.traineddata")
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tesseract-ocr/tesseract/main/LICENSE" -OutFile (Join-Path $OutputDir "LICENSE-tesseract.txt")
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/LICENSE" -OutFile (Join-Path $OutputDir "LICENSE-tessdata_fast.txt")

$tesseractExe = Join-Path $OutputDir "tesseract.exe"
if (-not (Test-Path $tesseractExe)) {
    throw "tesseract.exe was not found in $OutputDir after installation."
}

& $tesseractExe --version
Write-Host "Tesseract runtime written to $OutputDir"
