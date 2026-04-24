# Folder Batch and Legacy Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add recursive folder batch compression and real automation-backed support for `.xls`, `.ppt`, and `.hwp` output handling.

**Architecture:** Introduce explicit job/output planning so the engine can distinguish file jobs from folder-derived jobs. Keep the existing per-file compressor routing, but add folder scanning, output-root path planning, and real Windows automation adapters that convert `.xls` to `.xlsx`, `.ppt` to `.pptx`, and attempt same-format `.hwp` output.

**Tech Stack:** Python 3.12, PySide6, Pillow, pytest, PyInstaller, Windows COM automation (`pywin32` when installed), Ghostscript.

---

### Task 1: Folder Discovery and Output Planning Models

**Files:**
- Modify: `src/file_compressor/models.py`
- Create: `src/file_compressor/planning.py`
- Test: `tests/test_planning.py`

**Step 1: Write the failing test**

Add tests that define:

- a folder batch output root as `<folder>_압축됨`,
- preserved relative paths,
- converted output suffixes for `.xls -> .xlsx` and `.ppt -> .pptx`,
- unchanged `.hwp` suffix.

**Step 2: Run test to verify it fails**

Run: bundled Python with `pytest -p no:cacheprovider tests/test_planning.py -q`

Expected: FAIL because planning helpers do not exist.

**Step 3: Write minimal implementation**

Add:

- a job model that can carry `source`, `output`, and optional `batch_root`,
- planning helpers to compute sibling output roots and relative output paths,
- suffix conversion rules for legacy Office outputs.

**Step 4: Run test to verify it passes**

Run the same command and confirm PASS.

**Step 5: Commit**

```bash
git add tests/test_planning.py src/file_compressor/models.py src/file_compressor/planning.py
git commit -m "feat: add folder batch output planning"
```

---

### Task 2: Recursive Folder Input Expansion

**Files:**
- Modify: `src/file_compressor/formats.py`
- Modify: `src/file_compressor/engine.py`
- Create: `src/file_compressor/discovery.py`
- Test: `tests/test_discovery.py`

**Step 1: Write the failing test**

Add tests for:

- recursively finding supported files in nested folders,
- excluding unsupported files,
- returning deterministic source paths.

**Step 2: Run test to verify it fails**

Run: bundled Python with `pytest -p no:cacheprovider tests/test_discovery.py -q`

Expected: FAIL because folder discovery does not exist.

**Step 3: Write minimal implementation**

Add recursive folder discovery helpers that:

- accept a selected folder,
- walk subdirectories,
- keep only supported extensions,
- return sorted paths for stable UI/test behavior.

**Step 4: Run test to verify it passes**

Run the same command and confirm PASS.

**Step 5: Commit**

```bash
git add tests/test_discovery.py src/file_compressor/discovery.py src/file_compressor/formats.py src/file_compressor/engine.py
git commit -m "feat: add recursive folder discovery"
```

---

### Task 3: Engine Support for Planned Output Jobs

**Files:**
- Modify: `src/file_compressor/engine.py`
- Modify: `src/file_compressor/paths.py`
- Test: `tests/test_engine.py`

**Step 1: Write the failing test**

Extend engine tests to assert:

- file jobs keep existing next-to-source behavior,
- folder-derived jobs honor explicit output paths,
- batches continue after a planned-output failure.

**Step 2: Run test to verify it fails**

Run focused engine tests and confirm FAIL.

**Step 3: Write minimal implementation**

Update the engine so it can:

- accept planned output paths,
- avoid recomputing `_compressed` output paths when a planned output is already known,
- create parent directories for folder-derived outputs before compressing.

**Step 4: Run test to verify it passes**

Run focused engine tests and confirm PASS.

**Step 5: Commit**

```bash
git add tests/test_engine.py src/file_compressor/engine.py src/file_compressor/paths.py
git commit -m "feat: support planned output paths in engine"
```

---

### Task 4: Real Excel and PowerPoint Automation

**Files:**
- Modify: `src/file_compressor/compressors/windows_automation.py`
- Test: `tests/test_windows_automation.py`

**Step 1: Write the failing test**

Add tests that define:

- `.xls` conversion target becomes `.xlsx`,
- `.ppt` conversion target becomes `.pptx`,
- successful automation returns `COMPLETED` with the converted output path,
- missing dependencies still return `SKIPPED`.

**Step 2: Run test to verify it fails**

Run focused Windows automation tests and confirm FAIL.

**Step 3: Write minimal implementation**

Add automation helpers that:

- open Excel/PowerPoint via COM,
- save to modern format in the planned output location,
- close/release applications cleanly,
- return a completed result when conversion succeeds.

Then run the existing ZIP-based compression path on the converted file when needed.

**Step 4: Run test to verify it passes**

Run focused Windows automation tests and confirm PASS.

**Step 5: Commit**

```bash
git add tests/test_windows_automation.py src/file_compressor/compressors/windows_automation.py
git commit -m "feat: automate legacy office conversion"
```

---

### Task 5: HWP Automation Output Flow

**Files:**
- Modify: `src/file_compressor/compressors/windows_automation.py`
- Test: `tests/test_windows_automation.py`

**Step 1: Write the failing test**

Add tests that define:

- successful `.hwp` automation writes a same-format `.hwp` output,
- missing Hancom Office still returns `SKIPPED`,
- failed same-format save returns `FAILED` with a clear message.

**Step 2: Run test to verify it fails**

Run focused Windows automation tests and confirm FAIL.

**Step 3: Write minimal implementation**

Add Hancom automation flow that:

- opens the source `.hwp`,
- attempts same-format save to the planned output path,
- closes/releases the automation object,
- returns a clear failure when same-format save cannot be completed.

**Step 4: Run test to verify it passes**

Run focused Windows automation tests and confirm PASS.

**Step 5: Commit**

```bash
git add tests/test_windows_automation.py src/file_compressor/compressors/windows_automation.py
git commit -m "feat: add hwp automation output flow"
```

---

### Task 6: UI Folder Add Flow and Localization

**Files:**
- Modify: `src/file_compressor_app/ui.py`
- Modify: `src/file_compressor_app/view_model.py`
- Test: `tests/test_ui_options.py`
- Create: `tests/test_ui_folder_batch.py`

**Step 1: Write the failing test**

Add tests that define:

- a `폴더 추가` / `Add folder` button,
- folder selection expands into file rows,
- output paths for folder jobs point into `<folder>_압축됨`,
- localized labels and status messages remain correct.

**Step 2: Run test to verify it fails**

Run focused UI tests and confirm FAIL.

**Step 3: Write minimal implementation**

Update the UI to:

- add the folder button,
- call folder discovery/planning helpers,
- append planned jobs to the table,
- show folder-output paths in the output column,
- update localized status messages with the generated output root.

**Step 4: Run test to verify it passes**

Run focused UI tests and confirm PASS.

**Step 5: Commit**

```bash
git add tests/test_ui_options.py tests/test_ui_folder_batch.py src/file_compressor_app/ui.py src/file_compressor_app/view_model.py
git commit -m "feat: add folder batch ui flow"
```

---

### Task 7: Documentation and Full Verification

**Files:**
- Modify: `README.md`

**Step 1: Update README**

Document:

- folder batch behavior,
- `<folder>_압축됨` output-root naming,
- legacy output conversion rules,
- current automation requirements.

**Step 2: Run full test suite**

Run: bundled Python with `pytest -p no:cacheprovider tests -q`

Expected: PASS.

**Step 3: Run Qt smoke check**

Run the UI offscreen and confirm the folder button is present and default language is Korean.

**Step 4: Rebuild executable**

Run PyInstaller with `file-compressor.spec --noconfirm`.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update folder batch and automation usage"
```

---

## Notes for Execution

- Follow TDD strictly: write the focused failing test first for each task.
- Keep source folders untouched.
- Do not silently downgrade `.hwp` to another format.
- For COM automation, always close documents and quit/release application objects in success and failure paths.
- Preserve existing file-mode behavior while adding folder-mode behavior.
