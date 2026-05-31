# PDF Tools, Content Search, and OCR Design

## Goal

Add PDF page-management tools and file content search while keeping OCR as an optional dependency-based feature.

## PDF Tools

Add a `PDF 도구` / `PDF Tools` tab. It supports:

- Merge PDFs into one output file.
- Split every page into separate PDF files.
- Extract selected pages.
- Delete selected pages.
- Rotate selected pages.
- Reorder pages by an explicit page order.

The PDF tools use `pypdf`, which is bundled into the EXE. Users do not need to install a separate PDF program for these operations. All PDF-changing operations are preview-first and write to an output file/folder without overwriting existing files.

## Content Search

Add a `파일 내용 검색` / `Search` tab. It supports text search across:

- `.txt`, `.csv`, `.md`
- `.pdf` text layer
- `.docx`
- `.xlsx`, `.xlsm`, `.csv`

Search results show file name, type, match location, a short snippet, and status.

## OCR

OCR is conditional. The app detects the `tesseract` command and shows `OCR: 사용 가능` or `OCR: 설치 필요`.

If Tesseract is missing, OCR is not attempted and files that need OCR report `OCR 설치 필요`. If Tesseract is available, the search tab can run OCR for image files and can try OCR fallback for files without extractable text. The app provides an install button that opens the Tesseract Windows installer information page from the UB Mannheim project.

## Safety

PDF tools never overwrite existing files. Search and OCR do not modify files. OCR failures are reported per file instead of stopping the whole search.
