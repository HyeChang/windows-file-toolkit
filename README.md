# File Compressor

Windows desktop app for reducing the size of Excel, PowerPoint, PDF, HWPX, HWP, and legacy Office files.

The app preserves original files. Individual files are written next to the source file with `_compressed` in the file name. Folder batches are written under a newly planned sibling parent folder such as `원본폴더_압축됨`, preserving the original subfolder structure. If an output folder is selected, compressed results are written under that folder instead.

The main window is split into tabs:

- `문서 압축` / `Compression`: compress supported document files.
- `파일 이름 변경` / `Rename`: rename many files with preview-first rules.
- `파일 자동 분류` / `Classify`: move files into category folders.
- `파일 날짜 변경` / `Dates`: change file creation and modified dates.

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

## Folder Batches

Use `폴더 추가` / `Add folder` to add every supported document under a folder recursively.

- Outputs are grouped under a new sibling parent folder named `<folder>_압축됨`.
- If that folder already exists, the app plans `<folder>_압축됨_2`, `<folder>_압축됨_3`, and so on.
- Subfolders are preserved under the new output parent.
- Legacy `.xls` and `.ppt` files are converted to `.xlsx` and `.pptx` in the output batch.

## Output Folder

Use `출력 폴더 선택` / `Select output folder` to collect compressed files in a chosen location.

- Individual files are saved in the chosen folder with `_compressed` in the file name.
- Folder batches keep their relative subfolder structure under the chosen folder.
- Pending jobs are replanned when the output folder is selected after files have already been added.

## List Management

Use `선택 삭제` / `Remove selected` to remove selected rows from the queue, or `목록 비우기` / `Clear list` to reset the queue before starting compression.

## Batch Rename

Use the `파일 이름 변경` / `Rename` tab to add files or folders, configure rules, preview the result, and apply the changes.

- Prefix, suffix, find/replace, numbering, space cleanup, and Windows-invalid character cleanup are supported.
- Date normalization detects names such as `20260427`, `2026-04-27`, `2026.04.27`, `2026_04_27`, `2026년 4월 27일`, and `260427`.
- Date output formats include `YYYY-MM-DD_파일명`, `YYYYMMDD_파일명`, `파일명_YYYY-MM-DD`, and `파일명_YYYYMMDD`.
- Existing files are not overwritten. Collisions are resolved with `_2`, `_3`, and so on.
- `수정일 유지` / `Preserve modified date` is enabled by default, so renaming restores the original file modified timestamp after the rename.
- The detail panel shows the selected file's path, extension, size, creation date, modified date, planned name, and status.
- `되돌리기` / `Undo` restores the last applied rename when the original path is still available.

## File Classification

Use the `파일 자동 분류` / `Classify` tab to add files or folders, choose an output folder, preview destinations, and move files.

Files are grouped under category folders such as `PDF`, `Excel`, `PowerPoint`, `HWP`, `Images`, `Documents`, `Archives`, and `Other`. Existing files are not overwritten; name collisions are resolved with `_2`, `_3`, and so on.

The detail panel shows the selected file's metadata and planned destination. `되돌리기` / `Undo` moves the last applied batch back to its original paths when those paths are still available.

## File Dates

Use the `파일 날짜 변경` / `Dates` tab to change file timestamps after previewing the result.

- Creation date, modified date, or both can be changed.
- Dates can be entered directly, extracted from the file name, or set to the current time.
- File-name date extraction supports the same date patterns used by the rename tab.
- The detail panel shows the selected file's current metadata.
- `되돌리기` / `Undo` restores the previous creation and modified dates for the last applied batch.

Creation-date changes use the Windows file time API. On non-Windows systems, creation-date changes are reported as unsupported instead of being silently ignored.

## Progress and Results

The app shows overall progress, the current file being processed, and a cancel button while compression is running. Cancel stops before the next file starts; the file already being processed is allowed to finish safely.

The result table includes original size, compressed size, saved size, and saved rate for each file. A summary below the table shows completed/skipped/failed counts and total saved size/rate.

## Advanced Compression Settings

The desktop app includes three compression controls:

- Image size: `800 px`, `1200 px`, `1600 px`, or `Original`.
- JPEG quality: `50`, `65`, `78`, or `90`.
- PDF level: `Screen`, `Ebook`, `Printer`, or `High quality`.

Defaults are `1600 px`, JPEG quality `78`, and PDF level `Screen`.

## PDF Compression Tool

PDF compression uses Ghostscript. The app checks for Ghostscript on startup and shows the PDF tool status in the settings area. The environment diagnostics panel also checks Ghostscript, Microsoft Excel, Microsoft PowerPoint, and Hancom Office availability.

- If Ghostscript is available, PDF compression runs normally.
- If Ghostscript is missing, PDF files are skipped and the original files are preserved.
- Use the `설치` / `Install` button or `도구` / `Tools` menu to open the official Ghostscript download page.
- Use `다시 확인` / `Recheck` after installing supporting software to refresh the diagnostics without restarting the app.

## Language

The app supports Korean and English. Korean is selected by default, and the language selector changes the visible app labels, table headers, status text, and compression setting labels.

## Supported Formats

- `.xlsx`, `.xlsm`, `.pptx`, `.pptm`: direct ZIP-package image optimization.
- `.hwpx`: direct ZIP-package image optimization.
- `.pdf`: Ghostscript required; use the in-app install button or Tools menu if it is missing.
- `.hwp`: Hancom Office required; opened through Hancom automation and saved to the planned output path.
- `.xls`: Microsoft Excel required; converted to `.xlsx`, then optimized.
- `.ppt`: Microsoft PowerPoint required; converted to `.pptx`, then optimized.

When required desktop applications are not installed, the affected file is skipped with a clear status message.
