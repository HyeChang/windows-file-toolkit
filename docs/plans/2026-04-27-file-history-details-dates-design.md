# File History, Details, and Dates Design

## Goal

Add safer file-management workflows by showing selected-file details, allowing users to undo the last file action, and providing a dedicated tab for changing file creation and modified dates.

## UI Structure

The existing tabs stay intact and gain additional controls:

- `파일 이름 변경` / `Rename`: adds a detail panel and `되돌리기` button.
- `파일 자동 분류` / `Classify`: adds a detail panel and `되돌리기` button.
- `파일 날짜 변경` / `Dates`: new tab for changing creation date, modified date, or both.

The detail panel shows the selected file's name, full path, extension, size, creation date, modified date, planned output or destination, and status. If no row is selected, the panel shows a neutral empty state.

## Undo Model

Undo is scoped to the last successful apply action in each tab. It does not create a full permanent history database. This keeps behavior understandable and avoids storing long-lived sensitive file paths.

Undo rules:

- Rename undo moves `변경 후 파일` back to the original path.
- Classification undo moves `이동된 파일` back to the original path.
- Date-change undo restores the previous creation and modified timestamps.
- Undo never overwrites an existing file. If the original path is already occupied, undo fails for that file and reports the status.

## Date Change

The new date tab supports:

- Direct date/time input.
- Applying a date extracted from the file name.
- Applying the current time.
- Changing creation date only, modified date only, or both.

On Windows, creation date and modified date are changed through the Windows file time API. Modified date is also set with standard file timestamp behavior. If creation-date support is unavailable on a non-Windows system, the operation reports a clear failure instead of silently pretending it worked.

## Safety

All file-changing actions remain preview-first. Dropping or adding files only registers them. Date changes and undo actions report per-file status and do not overwrite existing files.
