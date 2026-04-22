# File Compressor Design

## Goal

Build a Windows desktop application that reduces file size for common office documents while preserving the original files.

## Approved Decisions

- App type: Windows desktop application.
- Output behavior: create a new file next to the original file, using a suffix such as `_compressed`.
- Original files must never be overwritten.
- Korean document support:
  - `.hwpx` is handled directly by the app.
  - `.hwp` is supported when Hancom Office is installed.
- First version prioritizes stable, practical compression over broad format coverage.

## Recommended Approach

Use Python with PySide6 for the desktop UI and a separate compression engine for file processing.

This approach keeps the UI simple, makes document processing libraries easy to use, and supports Windows automation for conditionally supported formats such as `.hwp`, `.xls`, and `.ppt`.

## Architecture

The app is split into three layers.

1. Desktop UI
   - Drag-and-drop file intake.
   - File picker button.
   - Job table with file name, type, original size, status, compressed size, and output path.
   - Start button.
   - Bottom status message.

2. Compression engine
   - Classifies input files by extension.
   - Chooses the correct compressor.
   - Generates safe output paths next to each source file.
   - Continues processing remaining files when one file fails.

3. Format adapters
   - Office Open XML adapter for `.xlsx`, `.xlsm`, `.pptx`, and `.pptm`.
   - HWPX adapter for `.hwpx`.
   - PDF adapter with Ghostscript detection.
   - Windows automation adapter for `.hwp`, `.xls`, and `.ppt` when the required desktop software is installed.

## Format Strategy

### `.xlsx`, `.xlsm`, `.pptx`, `.pptm`

These files are ZIP packages. The app opens the package, optimizes embedded files under media folders, and writes a new ZIP package that preserves the document structure.

Image optimization should:

- Downscale very large raster images.
- Re-encode JPEG and PNG files when this reduces size.
- Preserve unsupported or already-small files unchanged.

### `.hwpx`

HWPX is also ZIP based. The app uses the same package-level approach as Office Open XML files, with HWPX-specific media path detection when needed.

### `.pdf`

The app checks whether Ghostscript is available.

- If Ghostscript is available, the app uses it for practical PDF compression.
- If Ghostscript is missing, the app marks PDF compression as unavailable or limited and explains that installing Ghostscript improves PDF support.

### `.hwp`

The app checks whether Hancom Office automation is available on Windows.

- If Hancom Office is installed, the app can use an automation-based flow.
- If Hancom Office is missing, the file is marked as skipped because a required dependency is unavailable.

### `.xls`, `.ppt`

Legacy binary Office files are treated as conditional support.

- If Microsoft Office automation is available, a future path can convert them to modern formats and then compress.
- If Office automation is missing, they are skipped with a clear dependency message.

## User Flow

1. User opens the app.
2. User drops files into the window or clicks the file picker.
3. The app lists each selected file as `pending`.
4. User clicks `Start compression`.
5. The app processes files one by one.
6. Each completed file is written next to the original.
7. The table shows final status, compressed size, and output path.

## Status Model

- `pending`: waiting to be processed.
- `processing`: compression is currently running.
- `completed`: output file was created successfully.
- `skipped`: unsupported file or missing dependency.
- `failed`: unexpected error such as corrupt input, permission failure, or external tool failure.

## Output Naming

The output file is created next to the source file.

Example:

- Source: `report.pdf`
- Output: `report_compressed.pdf`

If the output path already exists, append a numeric suffix:

- `report_compressed_2.pdf`
- `report_compressed_3.pdf`

## Error Handling

Errors are isolated per file. One failed or skipped file must not stop the entire batch.

Dependency problems are reported as skipped jobs, not crashes.

Examples:

- PDF compression skipped because Ghostscript is missing.
- HWP compression skipped because Hancom Office is missing.
- Legacy Office compression skipped because Microsoft Office automation is missing.

## Testing Strategy

The compression engine is tested separately from the UI.

Initial tests cover:

- Safe output path generation.
- Numeric suffix generation when an output path already exists.
- Extension classification.
- ZIP-package compression preserves non-media document entries.
- Unsupported extensions are skipped.
- Missing dependency states are reported correctly.
- A failed job does not stop the rest of a batch.

## First Version Scope

Implemented compression:

- `.xlsx`
- `.xlsm`
- `.pptx`
- `.pptm`
- `.hwpx`
- `.pdf` when Ghostscript is installed

Conditional or guided support:

- `.hwp` when Hancom Office is installed
- `.xls` and `.ppt` when Microsoft Office is installed

Out of scope for the first version:

- Cloud upload or server-side compression.
- Editing original files in place.
- Guaranteed compression for every input file.
- Full standalone `.hwp` binary parsing without Hancom Office.
