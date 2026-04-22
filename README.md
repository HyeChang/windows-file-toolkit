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

## Supported Formats

- `.xlsx`, `.xlsm`, `.pptx`, `.pptm`: direct ZIP-package image optimization.
- `.hwpx`: direct ZIP-package image optimization.
- `.pdf`: Ghostscript required.
- `.hwp`: Hancom Office required.
- `.xls`, `.ppt`: Microsoft Office required.

Original files are not overwritten. Compressed files are written next to the source file with `_compressed` in the file name.
