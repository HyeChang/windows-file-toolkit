# Bundled Jpegtran Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Package `jpegtran.exe` inside the one-file Windows executable so JPEG lossless rotation works when the user carries only `FileCompressor.exe`.

**Architecture:** Keep the app's runtime lookup simple: prefer PyInstaller's extracted runtime directory, then the executable directory, then PATH. Keep `tools/jpegtran/jpegtran.exe` as the source-of-truth local binary path for development and packaging. Update the PyInstaller spec to include that file when present.

**Tech Stack:** Python 3.12, PyInstaller one-file, PySide6, pytest, `jpegtran`.

---

### Task 1: Runtime Detection

**Files:**
- Modify: `src/file_compressor/dependencies.py`
- Test: `tests/test_dependencies.py`

**Steps:**
1. Add a failing test that simulates `sys._MEIPASS` and expects `detect_jpegtran()` to prefer `tools/jpegtran/jpegtran.exe` inside that directory.
2. Update dependency detection to check a PyInstaller runtime directory before the executable directory and PATH.
3. Run `pytest tests/test_dependencies.py`.

### Task 2: PyInstaller Packaging

**Files:**
- Modify: `file-compressor.spec`
- Modify: `scripts/build_exe.ps1`
- Test: `tests/test_ocr_bundle_script.py` or a new focused test if needed

**Steps:**
1. Add the `tools/jpegtran/jpegtran.exe` data entry to the spec only when the file exists.
2. Make the build script print whether bundled JPEG rotation support will be included.
3. Run dependency and packaging-related tests.

### Task 3: Documentation and Build

**Files:**
- Modify: `README.md`
- Create or update: `tools/jpegtran/jpegtran.exe` when a verified binary is available

**Steps:**
1. Document that the final exe can include `jpegtran` internally.
2. Download or provide a Windows `jpegtran.exe` binary at `tools/jpegtran/jpegtran.exe`.
3. Run the full test suite.
4. Build `dist/FileCompressor.exe` and verify the output file hash.
