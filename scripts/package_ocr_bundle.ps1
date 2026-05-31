param(
    [string]$Python = $env:PYTHON,
    [string]$TesseractRoot = $env:TESSERACT_ROOT,
    [string]$OutputZip = "",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($Python)) {
    $Python = "python"
}
if ([string]::IsNullOrWhiteSpace($OutputZip)) {
    $OutputZip = Join-Path $projectRoot "dist/FileCompressor-OCR.zip"
}

function Resolve-TesseractRoot {
    param([string]$RequestedRoot)

    if (-not [string]::IsNullOrWhiteSpace($RequestedRoot)) {
        return (Resolve-Path $RequestedRoot).Path
    }

    $command = Get-Command "tesseract.exe" -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return (Split-Path -Parent $command.Source)
    }

    $candidates = @(
        (Join-Path $env:ProgramFiles "Tesseract-OCR")
    )
    if (-not [string]::IsNullOrWhiteSpace(${env:ProgramFiles(x86)})) {
        $candidates += (Join-Path ${env:ProgramFiles(x86)} "Tesseract-OCR")
    }

    foreach ($candidate in $candidates) {
        if (Test-Path (Join-Path $candidate "tesseract.exe")) {
            return $candidate
        }
    }

    throw "Tesseract root was not found. Pass -TesseractRoot or set TESSERACT_ROOT."
}

function Assert-TesseractBundle {
    param([string]$Root)

    $required = @(
        "tesseract.exe",
        "tessdata/kor.traineddata",
        "tessdata/eng.traineddata"
    )

    foreach ($relative in $required) {
        $target = Join-Path $Root $relative
        if (-not (Test-Path $target)) {
            throw "Required OCR bundle file is missing: $relative"
        }
    }
}

if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot "build_exe.ps1") -Python $Python
}

$exePath = Join-Path $projectRoot "dist/FileCompressor.exe"
if (-not (Test-Path $exePath)) {
    throw "FileCompressor.exe was not found. Build the executable first."
}

$resolvedTesseractRoot = Resolve-TesseractRoot $TesseractRoot
Assert-TesseractBundle $resolvedTesseractRoot

$staging = Join-Path $projectRoot "dist/ocr-bundle"
if (Test-Path $staging) {
    Remove-Item $staging -Recurse -Force
}
New-Item -ItemType Directory -Path $staging | Out-Null

Copy-Item $exePath (Join-Path $staging "FileCompressor.exe")
$targetTesseract = Join-Path $staging "tools/tesseract"
New-Item -ItemType Directory -Path $targetTesseract -Force | Out-Null
Copy-Item (Join-Path $resolvedTesseractRoot "*") $targetTesseract -Recurse -Force

$readme = @"
FileCompressor OCR Bundle

This package includes FileCompressor.exe and a local Tesseract OCR runtime under tools/tesseract.
The app checks tools/tesseract/tesseract.exe before looking for a system Tesseract installation.

Extract this zip as a folder, then run FileCompressor.exe from the extracted folder.
No system Tesseract install, D:\ocr folder, or fixed drive path is required on the target computer.

Required OCR data included:
- tessdata/kor.traineddata
- tessdata/eng.traineddata

License notices for Tesseract and traineddata should be distributed with this bundle.
"@
Set-Content -Path (Join-Path $staging "README-OCR.txt") -Value $readme -Encoding UTF8

if (Test-Path $OutputZip) {
    Remove-Item $OutputZip -Force
}
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $OutputZip -Force

Write-Host "OCR bundle written to $OutputZip"
