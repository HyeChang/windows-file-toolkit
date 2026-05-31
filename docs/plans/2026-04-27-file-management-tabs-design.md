# File Management Tabs Design

## Goal

Add file-management tools alongside the existing document compressor without mixing workflows in one screen.

## UI Structure

Use a top-level tab layout:

- `문서 압축` / `Compress`: existing compression workflow.
- `파일 이름 변경` / `Rename`: batch rename with preview and safe apply.
- `파일 자동 분류` / `Classify`: move files into category folders with preview and safe apply.

The existing compressor controls remain unchanged inside the first tab.

## Rename Tool

The rename tab supports file/folder input, preview, and apply. Supported operations:

- Prefix and suffix.
- Find/replace.
- Clean file names by normalizing spaces and removing Windows-invalid characters.
- Numbering.
- Date normalization from file names.

Date patterns detected:

- `YYYYMMDD`
- `YYYY-MM-DD`
- `YYYY.MM.DD`
- `YYYY_MM_DD`
- `YYYY년 M월 D일`
- `YYMMDD`

Date output formats:

- `YYYY-MM-DD_파일명`
- `YYYYMMDD_파일명`
- `파일명_YYYY-MM-DD`
- `파일명_YYYYMMDD`

If a date normalization mode is selected and a file has no date, the date part is skipped rather than inventing a date.

Modification time preservation is enabled by default. The implementation records the original modified time before rename and restores it with `os.utime` after rename.

## Classification Tool

The classification tab supports file/folder input, preview, and apply. Files are moved under a user-selected output folder by category:

- `PDF`
- `Excel`
- `PowerPoint`
- `HWP`
- `Images`
- `Documents`
- `Archives`
- `Other`

Name collisions are resolved by appending `_2`, `_3`, and so on. Files are not overwritten.

## Safety

- No destructive action runs without preview.
- Existing files are not overwritten.
- Apply actions report per-file status.
- Rename preserves modification time by default.
- Classification uses safe collision naming.

