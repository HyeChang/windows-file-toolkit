# File Tool Drag and Drop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add drag-and-drop file and folder registration to the rename and classify tabs.

**Architecture:** Extend `FileToolTable` so it can accept local file URL drops and call a tab-provided callback. Wire `RenameToolWidget` and `ClassifyToolWidget` tables to their existing `add_paths` methods.

**Tech Stack:** Python 3.12, PySide6, pytest.

---

### Task 1: Drag and Drop Tests

**Files:**
- Modify: `tests/test_file_tools_ui.py`

**Steps:**
1. Add failing tests that drop local file URLs onto the rename and classify tables.
2. Verify each dropped file is added to the corresponding tab.
3. Verify dropped folders are expanded through existing `add_paths` behavior.
4. Run `pytest tests/test_file_tools_ui.py -q` and confirm failure because the table does not yet accept drops.

### Task 2: Table Drop Support

**Files:**
- Modify: `src/file_compressor_app/file_tools_ui.py`

**Steps:**
1. Add optional `on_files` callback support to `FileToolTable`.
2. Enable drops when a callback is supplied.
3. Implement `dragEnterEvent`, `dragMoveEvent`, and `dropEvent` for local file URLs.
4. Wire rename/classify tables with `self.add_paths`.
5. Run focused UI tests.

### Task 3: Verification and EXE

**Files:**
- Build artifact: `dist/FileCompressor.exe`

**Steps:**
1. Run the full test suite.
2. Rebuild the executable.
3. Copy the executable to the root `dist` folder.
4. Commit the changes.
