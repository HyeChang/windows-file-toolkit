# PDF Search OCR Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add PDF page tools, file content search, and optional OCR integration.

**Architecture:** Add pure PDF utilities in `src/file_compressor/pdf_tools.py`, pure content search utilities in `src/file_compressor/content_search.py`, and OCR detection in `src/file_compressor/dependencies.py`. Add PySide widgets in `src/file_compressor_app/pdf_search_ui.py` and mount them from `src/file_compressor_app/ui.py`.

**Tech Stack:** Python 3.12, PySide6, pypdf, python-docx, openpyxl, pytest, optional Tesseract CLI.

---

### Task 1: PDF Tools Backend

**Files:**
- Create: `src/file_compressor/pdf_tools.py`
- Test: `tests/test_pdf_tools.py`
- Modify: `pyproject.toml`

**Step 1: Write failing tests**

Add tests for merge, split, extract, delete, rotate, reorder, page-range parsing, and collision-safe output paths.

Run: `pytest tests/test_pdf_tools.py -q`
Expected: FAIL because `file_compressor.pdf_tools` does not exist.

**Step 2: Implement backend**

Use `pypdf.PdfReader` and `pypdf.PdfWriter`. Add `PdfOperationResult`, `parse_page_selection`, `merge_pdfs`, `split_pdf`, `extract_pages`, `delete_pages`, `rotate_pages`, and `reorder_pages`.

**Step 3: Verify**

Run: `pytest tests/test_pdf_tools.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: add pdf page tools`

### Task 2: Content Search and OCR Backend

**Files:**
- Create: `src/file_compressor/content_search.py`
- Modify: `src/file_compressor/dependencies.py`
- Test: `tests/test_content_search.py`

**Step 1: Write failing tests**

Add tests for text file search, PDF text search, DOCX search, XLSX search, no-match behavior, OCR detector, and OCR fallback command invocation.

Run: `pytest tests/test_content_search.py -q`
Expected: FAIL because content search functions do not exist.

**Step 2: Implement backend**

Add `SearchResult`, `search_files`, `extract_text_from_file`, `search_text`, `run_tesseract_ocr`, `detect_tesseract`, and `TESSERACT_DOWNLOAD_URL`.

**Step 3: Verify**

Run: `pytest tests/test_content_search.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: add content search and ocr detection`

### Task 3: PDF Tools and Search UI

**Files:**
- Create: `src/file_compressor_app/pdf_search_ui.py`
- Modify: `src/file_compressor_app/ui.py`
- Test: `tests/test_pdf_search_ui.py`

**Step 1: Write failing UI tests**

Add tests for:
- Main window includes `PDF 도구` and `파일 내용 검색` tabs.
- PDF tool preview/apply for extract pages.
- Search tab finds text in a text file.
- OCR status and install button are localized.

Run: `pytest tests/test_pdf_search_ui.py -q`
Expected: FAIL because tabs/widgets do not exist.

**Step 2: Implement UI**

Add `PdfToolsWidget` and `ContentSearchWidget` with drag-and-drop file lists, preview/apply/search controls, result tables, and OCR install action.

**Step 3: Verify**

Run: `pytest tests/test_pdf_search_ui.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: add pdf tools and content search tabs`

### Task 4: Documentation, Full Verification, and EXE

**Files:**
- Modify: `README.md`
- Build artifact: `dist/FileCompressor.exe`

**Step 1: Update README**

Document PDF tools, content search, OCR behavior, and the Tesseract install button.

**Step 2: Run full tests**

Run: `pytest tests -q`
Expected: all tests pass.

**Step 3: Rebuild EXE**

Run: `scripts/build_exe.ps1`
Expected: build completes.

**Step 4: Copy root EXE**

Copy the worktree EXE to `D:\Work\workspace\codex\fileCompress\dist\FileCompressor.exe`.

**Step 5: Commit docs**

Commit message: `docs: document pdf search and ocr tools`
