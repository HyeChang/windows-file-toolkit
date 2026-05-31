# Folder Batch and Legacy Automation Design

## Goal

Extend the desktop file compressor so users can add folders for recursive batch processing and get real automation-backed handling for legacy Office files, while preserving source files and directory structure.

## Approved Decisions

- Add folder selection to the desktop app.
- When a folder is added, process supported files recursively.
- Do not write compressed files next to the originals for folder jobs.
- Instead, create a new sibling output root named `<source-folder>_압축됨`.
- Preserve the original subfolder structure under that new output root.
- Keep original source files and source folders untouched.
- Legacy output policy:
  - `.xls` should be converted to `.xlsx`.
  - `.ppt` should be converted to `.pptx`.
  - `.hwp` should stay as `.hwp` when automation allows stable same-format save.

## Recommended Approach

Extend the existing compression engine rather than introducing a separate batch pipeline.

The current app already has a clean file-based flow:

- UI gathers inputs.
- Engine classifies files and routes to a compressor.
- Format adapters perform the actual work.

The new feature fits naturally by adding folder discovery, output-root planning, and real automation adapters for legacy formats.

## Architecture

The implementation is split into four parts.

1. Input collection
   - The UI adds a `폴더 추가` / `Add folder` action.
   - Folder selection expands into individual file jobs for supported file types.

2. Output planning
   - File jobs keep the existing output rule: write next to the original using `_compressed`.
   - Folder jobs create a sibling root `<folder>_압축됨`.
   - Each output file is written under that root using the original relative path.

3. Compression engine
   - The engine accepts a richer job or output target description.
   - It computes the correct output path before dispatching to a file-format adapter.

4. Format adapters
   - ZIP-based formats continue to use the existing compressor.
   - PDF continues to use Ghostscript when available.
   - Legacy Office and HWP move from detection-only adapters to real automation flows.

## Folder Processing Flow

For a selected folder:

1. Recursively scan the directory tree.
2. Keep only supported file types.
3. For each supported file:
   - record the source path,
   - compute the relative path from the selected folder,
   - compute the output path inside `<source-folder>_압축됨`.
4. Display each file as its own row in the job table.
5. Compress rows one by one using the existing batch behavior.

Example:

- Source folder: `D:\자료\문서`
- Output root: `D:\자료\문서_압축됨`
- Source file: `D:\자료\문서\하위폴더\발표.ppt`
- Output file: `D:\자료\문서_압축됨\하위폴더\발표.pptx`

## Legacy Automation Strategy

### `.xls`

- Detect Microsoft Excel registration.
- Open the workbook through Excel automation.
- Save to `.xlsx`.
- Run the normal ZIP-based compression path on the generated `.xlsx`.

### `.ppt`

- Detect Microsoft PowerPoint registration.
- Open the presentation through PowerPoint automation.
- Save to `.pptx`.
- Run the normal ZIP-based compression path on the generated `.pptx`.

### `.hwp`

- Detect Hancom Office registration.
- Open the document through Hancom automation.
- Attempt same-format `.hwp` save into the planned output path.
- If stable same-format save is unavailable, return a clear failure or unsupported message instead of silently downgrading to another format.

## UI Changes

Add:

- `폴더 추가` / `Add folder` button beside the existing file-add button.
- Output path display that reflects either:
  - next-to-source file output, or
  - folder-output-root path.

Status messaging should include the generated folder-output root when a folder batch is prepared or completed.

## Error Handling

- A failed file must not stop the rest of the batch.
- If an automation dependency is missing:
  - `.xls` / `.ppt` should report that Microsoft Office is required.
  - `.hwp` should report that Hancom Office is required.
- If an automation save/convert step fails, return a failure for that file only.
- Folder output roots should be created lazily and only as needed.

## Testing Strategy

Add tests for:

- Recursive supported-file discovery.
- Folder output-root naming.
- Relative-path preservation under `<source-folder>_압축됨`.
- `.xls` output path conversion to `.xlsx`.
- `.ppt` output path conversion to `.pptx`.
- UI folder-add flow.
- Engine routing for file jobs versus folder-derived jobs.

## Out of Scope

- Merging multiple selected folders into one shared output root.
- Concurrent compression workers.
- In-place modification of source folders.
- Automatic `.hwp` fallback conversion to another format without explicit approval.
