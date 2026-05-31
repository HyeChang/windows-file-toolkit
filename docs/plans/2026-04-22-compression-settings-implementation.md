# Compression Settings Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add advanced compression controls for image resolution, JPEG quality, and PDF compression level.

**Architecture:** Introduce a `CompressionOptions` model shared by the engine, format compressors, and UI. The UI creates options from combo boxes and passes them through `compress_file`; ZIP-based documents use image settings and PDF compression uses the selected Ghostscript preset.

**Tech Stack:** Python 3.12, PySide6, Pillow, pytest, PyInstaller.

---

### Task 1: Compression Options Model

**Files:**
- Modify: `src/file_compressor/models.py`
- Test: `tests/test_options.py`

**Step 1: Write the failing test**

Assert default options are `max_image_dimension=1600`, `jpeg_quality=78`, and `pdf_preset="screen"`.

**Step 2: Run test to verify it fails**

Run: bundled Python with `pytest -p no:cacheprovider tests/test_options.py -q`.

**Step 3: Implement minimal model**

Add a frozen `CompressionOptions` dataclass to `models.py`.

**Step 4: Run test to verify it passes**

Run the same test command.

### Task 2: Pass Options Through Engine and ZIP Compressor

**Files:**
- Modify: `src/file_compressor/engine.py`
- Modify: `src/file_compressor/compressors/package.py`
- Modify: `src/file_compressor/compressors/windows_automation.py`
- Test: `tests/test_package_compressors.py`
- Test: `tests/test_engine.py`

**Step 1: Write failing tests**

Assert `compress_zip_document` forwards custom max dimension and JPEG quality to the image optimizer, and `compress_many` accepts options.

**Step 2: Run tests to verify they fail**

Run focused tests.

**Step 3: Implement option plumbing**

Add optional `options` parameters defaulting to `CompressionOptions()`.

**Step 4: Run focused tests**

Confirm focused tests pass.

### Task 3: PDF Preset Support

**Files:**
- Modify: `src/file_compressor/compressors/pdf.py`
- Test: `tests/test_pdf_compressor.py`

**Step 1: Write failing test**

Assert a `CompressionOptions(pdf_preset="ebook")` command includes `-dPDFSETTINGS=/ebook`.

**Step 2: Run test to verify it fails**

Run focused PDF tests.

**Step 3: Implement preset mapping**

Pass options to `compress_pdf` and `build_ghostscript_command`.

**Step 4: Run focused tests**

Confirm PDF tests pass.

### Task 4: UI Controls

**Files:**
- Modify: `src/file_compressor_app/ui.py`
- Test: `tests/test_ui_options.py`

**Step 1: Write failing test**

Instantiate `MainWindow` in offscreen Qt and assert selected combo values produce a `CompressionOptions` instance.

**Step 2: Run test to verify it fails**

Run focused UI option test.

**Step 3: Implement controls**

Add combo boxes for image maximum resolution, JPEG quality, and PDF preset. Use `current_options()` when calling `compress_file`.

**Step 4: Run focused tests**

Confirm UI option tests pass.

### Task 5: Documentation, Full Verification, and Rebuild

**Files:**
- Modify: `README.md`

**Step 1: Update README**

Document advanced settings and defaults.

**Step 2: Run all tests**

Run bundled Python with `pytest -p no:cacheprovider tests -q`.

**Step 3: Run Qt smoke check**

Instantiate `MainWindow` with `QT_QPA_PLATFORM=offscreen`.

**Step 4: Rebuild executable**

Run PyInstaller against `file-compressor.spec`.
