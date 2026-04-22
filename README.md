# File Compressor

Windows desktop app for reducing the size of Excel, PowerPoint, PDF, HWPX, and conditionally supported HWP files.

The app preserves original files and writes compressed copies next to the source file.

## Run from Source

```powershell
python -m pip install -e ".[dev]"
python -m file_compressor_app.main
```

## Build Executable

```powershell
$env:PYTHON = "C:\Path\To\python.exe"
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

The executable is written to `dist/FileCompressor.exe`.

## Advanced Compression Settings

The desktop app includes three compression controls:

- Image size: `800 px`, `1200 px`, `1600 px`, or `Original`.
- JPEG quality: `50`, `65`, `78`, or `90`.
- PDF level: `Screen`, `Ebook`, `Printer`, or `High quality`.

Defaults are `1600 px`, JPEG quality `78`, and PDF level `Screen`.

## Supported Formats

- `.xlsx`, `.xlsm`, `.pptx`, `.pptm`: direct ZIP-package image optimization.
- `.hwpx`: direct ZIP-package image optimization.
- `.pdf`: Ghostscript required.
- `.hwp`: recognized and reported as requiring Hancom Office; full automation compression is not implemented in this version.
- `.xls`, `.ppt`: recognized and reported as requiring Microsoft Office; full automation compression is not implemented in this version.

Original files are not overwritten. Compressed files are written next to the source file with `_compressed` in the file name.
