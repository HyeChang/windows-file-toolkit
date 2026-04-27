# PDF Tools Accessibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve PDF tools by adding visible page-level input and output previews, with a dedicated two-PDF merge workflow.

**Architecture:** Extend `src/file_compressor/pdf_tools.py` with page-reference and preview-plan helpers. Refactor `PdfToolsWidget` in `src/file_compressor_app/pdf_search_ui.py` to show merge input panels, merge result rows, and single-PDF operation plan rows. Keep existing pypdf write functions and add an apply helper that writes the visible merge result order.

**Tech Stack:** Python 3.12, PySide6, pypdf, pytest.

---

### Task 1: Page Plan Backend

**Files:**
- Modify: `src/file_compressor/pdf_tools.py`
- Test: `tests/test_pdf_tools.py`

**Step 1: Write failing tests**

Add tests for:
- `pdf_page_refs(path)` returns one row per source page.
- `default_merge_plan([pdf1, pdf2])` returns PDF 1 pages followed by PDF 2 pages.
- `write_page_plan(plan, output)` writes pages in visible plan order.
- `build_single_pdf_plan(...)` marks extract/delete/split/rotate/reorder actions correctly.

Run: `pytest tests/test_pdf_tools.py -q`
Expected: FAIL because page plan functions do not exist.

**Step 2: Implement backend helpers**

Add:
- `PdfPageRef`
- `PdfPagePlan`
- `pdf_page_refs`
- `default_merge_plan`
- `write_page_plan`
- `build_single_pdf_plan`

**Step 3: Verify**

Run: `pytest tests/test_pdf_tools.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: add pdf page planning`

### Task 2: Merge Preview UI

**Files:**
- Modify: `src/file_compressor_app/pdf_search_ui.py`
- Test: `tests/test_pdf_search_ui.py`

**Step 1: Write failing tests**

Add tests for:
- Merge mode keeps only two PDFs.
- `pdf1_table`, `pdf2_table`, and `merge_result_table` show page rows.
- Default merge result is PDF 1 pages followed by PDF 2 pages.
- Moving a merge result row changes output order.
- Applying merge writes pages in the merge result order.

Run: `pytest tests/test_pdf_search_ui.py -q`
Expected: FAIL because merge panels do not exist.

**Step 2: Implement merge UI**

Add three tables to `PdfToolsWidget`, show/hide them for merge mode, build page rows from `default_merge_plan`, add result-row move/remove helpers, and apply merge from `self.merge_plan`.

**Step 3: Verify**

Run: `pytest tests/test_pdf_search_ui.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: improve pdf merge preview`

### Task 3: Single-PDF Operation Preview UI

**Files:**
- Modify: `src/file_compressor_app/pdf_search_ui.py`
- Test: `tests/test_pdf_search_ui.py`

**Step 1: Write failing tests**

Add tests for:
- Extract preview shows included/excluded pages.
- Delete preview shows kept/deleted pages.
- Split preview shows per-page output names.
- Rotate preview shows selected page rotations.
- Reorder preview shows resulting order.

Run: `pytest tests/test_pdf_search_ui.py -q`
Expected: FAIL for missing page-plan table behavior.

**Step 2: Implement single-PDF UI**

Add `page_plan_table`, populate it from `build_single_pdf_plan`, and apply operations using the visible operation settings.

**Step 3: Verify**

Run: `pytest tests/test_pdf_search_ui.py -q`
Expected: PASS.

**Step 4: Commit**

Commit message: `feat: improve pdf operation previews`

### Task 4: Documentation, Full Verification, and EXE

**Files:**
- Modify: `README.md`
- Build artifact: `dist/FileCompressor.exe`

**Step 1: Update README**

Document the merge panels, two-PDF merge limit, and page-level previews.

**Step 2: Run full tests**

Run: `pytest tests -q`
Expected: all tests pass.

**Step 3: Rebuild EXE**

Run: `scripts/build_exe.ps1`
Expected: build completes.

**Step 4: Copy root EXE**

Copy the worktree EXE to `D:\Work\workspace\codex\fileCompress\dist\FileCompressor.exe`.

**Step 5: Commit docs**

Commit message: `docs: document pdf preview workflow`
