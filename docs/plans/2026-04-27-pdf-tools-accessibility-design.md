# PDF Tools Accessibility Design

## Goal

Make PDF tools understandable before execution by showing page-level inputs and page-level output plans.

## Problem

The current PDF tools tab exposes operations and page text fields, but it does not show which pages are affected or how the final PDF will be composed. Users cannot confidently verify merge order, deleted pages, split outputs, rotations, or reorder results before pressing apply.

## Merge UI

Merge becomes a dedicated two-file workflow:

- The merge operation accepts at most two PDFs.
- The left panel shows `PDF 1` pages.
- The middle panel shows `PDF 2` pages.
- The right panel shows `병합 결과` / `Merge Result`.
- The merge result defaults to all pages from PDF 1, then all pages from PDF 2.
- The result table shows result order, source file, source page, rotation, and output status.
- Users can add selected pages from either input, remove result rows, and move result rows up/down.
- Applying merge writes pages exactly in the result table order.

If more than two PDFs are added in merge mode, only the first two PDFs are kept for the merge page panels.

## Single-PDF Operations UI

Delete, split, extract, rotate, and reorder use a single page-plan table:

- Each page row shows original page number, action, rotation, and output.
- Extract marks selected pages as included and others as excluded.
- Delete marks selected pages as deleted and others as kept.
- Split shows one output file per page.
- Rotate shows selected pages with the rotation angle.
- Reorder shows the resulting page order.

## Safety

No PDF is modified in place. Outputs still use collision-safe paths. Preview tables are the source of truth for apply actions, so the visible plan and generated PDF stay aligned.
