# File History, Details, and Dates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add selected-file detail panels, per-tab undo for file-management actions, and a file date change tab for creation/modified timestamps.

**Architecture:** Extend pure file operations in `src/file_compressor/file_tools.py` so timestamp changes and undo behavior can be tested without UI. Add reusable detail-panel and date-tab widgets in `src/file_compressor_app/file_tools_ui.py`, then mount the date tab from `src/file_compressor_app/ui.py`.

**Tech Stack:** Python 3.12, PySide6, pytest, Windows file time API through `ctypes`.

---

### Task 1: Timestamp and Undo Backend

**Files:**
- Modify: `src/file_compressor/file_tools.py`
- Test: `tests/test_file_tools.py`

**Step 1: Write failing backend tests**

Add tests for:
- Reading and setting modified/created timestamps.
- Applying a date-change plan and restoring it with undo.
- Undoing completed rename results without overwriting occupied original paths.
- Undoing completed classification results without overwriting occupied original paths.

Run: `pytest tests/test_file_tools.py -q`
Expected: FAIL because timestamp and undo functions do not exist.

**Step 2: Implement minimal backend**

Add:
- `FileTimestamps`
- `DateChangeOptions`
- `DateChangePlan`
- `get_file_timestamps`
- `set_file_timestamps`
- `build_date_change_plan`
- `apply_date_change_plan`
- `undo_rename_results`
- `undo_classification_results`
- `undo_date_change_results`

**Step 3: Verify backend**

Run: `pytest tests/test_file_tools.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: add file undo and timestamp operations`

### Task 2: Detail Panel and Undo UI

**Files:**
- Modify: `src/file_compressor_app/file_tools_ui.py`
- Test: `tests/test_file_tools_ui.py`

**Step 1: Write failing UI tests**

Add tests for:
- Rename tab detail panel showing selected file details and planned new name.
- Classify tab detail panel showing selected file details and planned destination.
- Rename tab undo button restoring the previous path.
- Classify tab undo button restoring the previous path.

Run: `pytest tests/test_file_tools_ui.py -q`
Expected: FAIL because the panel and undo button do not exist.

**Step 2: Implement UI**

Add reusable `FileDetailPanel`, connect table selection changes to panel refresh, add `undo_button`, and wire it to backend undo functions.

**Step 3: Verify focused UI**

Run: `pytest tests/test_file_tools_ui.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: add file detail panels and undo controls`

### Task 3: Date Change Tab

**Files:**
- Modify: `src/file_compressor_app/file_tools_ui.py`
- Modify: `src/file_compressor_app/ui.py`
- Test: `tests/test_file_tools_ui.py`

**Step 1: Write failing UI tests**

Add tests for:
- Main window includes `파일 날짜 변경` / `Dates` tab.
- Date tab previews manual creation/modified changes.
- Date tab can use file-name date extraction.
- Date tab apply and undo restore timestamps.

Run: `pytest tests/test_file_tools_ui.py -q`
Expected: FAIL because the date tab does not exist.

**Step 2: Implement date tab**

Add `DateChangeToolWidget`, date source controls, creation/modified checkboxes, preview/apply/undo actions, and detail panel.

**Step 3: Verify focused UI**

Run: `pytest tests/test_file_tools_ui.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: add file date change tab`

### Task 4: Docs, Full Verification, and EXE

**Files:**
- Modify: `README.md`
- Build artifact: `dist/FileCompressor.exe`

**Step 1: Update README**

Document the detail panel, undo behavior, and file date tab.

**Step 2: Run full tests**

Run: `pytest tests -q`
Expected: all tests pass.

**Step 3: Rebuild EXE**

Run: `scripts/build_exe.ps1`
Expected: build completes and writes `dist/FileCompressor.exe`.

**Step 4: Copy root EXE**

Copy the worktree EXE to `D:\Work\workspace\codex\fileCompress\dist\FileCompressor.exe`.

**Step 5: Commit README if changed**

Commit message: `docs: document file history and date tools`
