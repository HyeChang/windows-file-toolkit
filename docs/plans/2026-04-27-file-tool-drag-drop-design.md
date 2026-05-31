# File Tool Drag and Drop Design

## Goal

Allow users to register files and folders by dragging them onto the file list tables in the `파일 이름 변경` and `파일 자동 분류` tabs.

## Design

The existing compression tab already supports table-based drag and drop. The new file-management tabs will use the same interaction pattern: the table is the drop target, and dropped local file URLs are converted to `Path` objects and passed to each tab's existing `add_paths` method.

Folder drops follow the same behavior as each tab's `폴더 추가` button: folders are expanded recursively into files. Duplicate files remain ignored by the existing `add_paths` logic. Any active preview is cleared when new files are added, so users can regenerate a preview from the updated list.

## Safety

Only local file URLs are accepted. Dropping files never renames or moves anything by itself; it only adds rows to the pending list. Apply actions still require the user to preview and press `적용`.
