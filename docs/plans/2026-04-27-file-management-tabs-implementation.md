# File Management Tabs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add file rename and file classification tabs with preview-first workflows, date normalization, and modification-time preservation.

**Architecture:** Keep compression behavior in the existing `MainWindow` while wrapping it in a `QTabWidget`. Add pure file-management logic in `src/file_compressor/file_tools.py`, then add PySide widgets in `src/file_compressor_app/file_tools_ui.py` and mount them as tabs.

**Tech Stack:** Python 3.12, PySide6, pytest.

---

### Task 1: Pure File Rename Logic

**Files:**
- Create: `src/file_compressor/file_tools.py`
- Test: `tests/test_file_tools.py`

**Steps:**
1. Write failing tests for date extraction, `파일명_YYYYMMDD` formatting, clean-name behavior, collision-safe targets, and modified-time preservation.
2. Implement `RenameOptions`, `RenamePlan`, `build_rename_plan`, `apply_rename_plan`, and date parsing helpers.
3. Run `pytest tests/test_file_tools.py -q`.
4. Commit.

### Task 2: Pure Classification Logic

**Files:**
- Modify: `src/file_compressor/file_tools.py`
- Test: `tests/test_file_tools.py`

**Steps:**
1. Write failing tests for extension category mapping and collision-safe destination paths.
2. Implement `ClassificationPlan`, `classify_file_category`, `build_classification_plan`, and `apply_classification_plan`.
3. Run `pytest tests/test_file_tools.py -q`.
4. Commit.

### Task 3: Add Tabs and Rename UI

**Files:**
- Create: `src/file_compressor_app/file_tools_ui.py`
- Modify: `src/file_compressor_app/ui.py`
- Test: `tests/test_file_tools_ui.py`

**Steps:**
1. Write failing tests for tab labels, rename preview, date normalization option `파일명_YYYYMMDD`, and apply preserving modified time.
2. Add `QTabWidget` to `MainWindow`.
3. Move existing compression layout into the first tab.
4. Add `RenameToolWidget` with add files/folder, options, preview table, and apply button.
5. Run focused UI tests.
6. Commit.

### Task 4: Add Classification UI

**Files:**
- Modify: `src/file_compressor_app/file_tools_ui.py`
- Test: `tests/test_file_tools_ui.py`

**Steps:**
1. Write failing tests for category preview and output folder selection.
2. Add `ClassifyToolWidget` with add files/folder, output folder, preview table, and apply button.
3. Run focused UI tests.
4. Commit.

### Task 5: Documentation, Full Verification, and EXE

**Files:**
- Modify: `README.md`

**Steps:**
1. Document the new tabs and safe preview/apply behavior.
2. Run the full test suite.
3. Rebuild `dist/FileCompressor.exe`.
4. Copy the EXE to the root `dist` folder.
5. Commit documentation if not already committed.

