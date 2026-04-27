from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader


TEXT_SUFFIXES = {".txt", ".csv", ".md", ".log"}
PDF_SUFFIXES = {".pdf"}
DOCX_SUFFIXES = {".docx"}
XLSX_SUFFIXES = {".xlsx", ".xlsm"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


@dataclass(frozen=True)
class TextSection:
    kind: str
    location: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    source: Path
    kind: str
    location: str
    snippet: str
    status: str
    message: str = ""


def extract_text_from_file(path: Path) -> list[TextSection]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _extract_text_file(path)
    if suffix in PDF_SUFFIXES:
        return _extract_pdf(path)
    if suffix in DOCX_SUFFIXES:
        return _extract_docx(path)
    if suffix in XLSX_SUFFIXES:
        return _extract_xlsx(path)
    raise ValueError("Unsupported file type.")


def search_files(
    paths: list[Path],
    query: str,
    *,
    use_ocr: bool = False,
    tesseract_executable: str | None = None,
    ocr_runner=subprocess.run,
) -> list[SearchResult]:
    results: list[SearchResult] = []
    query_normalized = query.lower()
    for path in paths:
        path = Path(path)
        try:
            sections = extract_text_from_file(path)
        except ValueError:
            if use_ocr and path.suffix.lower() in IMAGE_SUFFIXES | PDF_SUFFIXES:
                results.extend(
                    _search_ocr(path, query_normalized, tesseract_executable, ocr_runner)
                )
            else:
                results.append(
                    SearchResult(
                        source=path,
                        kind=_kind_for_path(path),
                        location="-",
                        snippet="",
                        status="skipped",
                        message="Unsupported file type.",
                    )
                )
            continue
        except Exception as exc:
            results.append(
                SearchResult(
                    source=path,
                    kind=_kind_for_path(path),
                    location="-",
                    snippet="",
                    status="failed",
                    message=str(exc),
                )
            )
            continue

        matched = _search_sections(path, sections, query_normalized)
        if matched:
            results.extend(matched)
        elif use_ocr and path.suffix.lower() in IMAGE_SUFFIXES | PDF_SUFFIXES:
            results.extend(_search_ocr(path, query_normalized, tesseract_executable, ocr_runner))
        else:
            results.append(
                SearchResult(
                    source=path,
                    kind=_kind_for_path(path),
                    location="-",
                    snippet="",
                    status="no_match",
                )
            )
    return results


def run_tesseract_ocr(
    path: Path,
    *,
    executable: str = "tesseract",
    language: str = "kor+eng",
    runner=subprocess.run,
) -> str:
    command = [executable, str(path), "stdout", "-l", language]
    result = runner(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or "Tesseract OCR failed.")
    return result.stdout


def _extract_text_file(path: Path) -> list[TextSection]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    sections: list[TextSection] = []
    for index, line in enumerate(text.splitlines(), start=1):
        sections.append(TextSection(kind="Text", location=f"Line {index}", text=line))
    return sections


def _extract_pdf(path: Path) -> list[TextSection]:
    reader = PdfReader(str(path))
    sections: list[TextSection] = []
    for index, page in enumerate(reader.pages, start=1):
        sections.append(TextSection(kind="PDF", location=f"Page {index}", text=page.extract_text() or ""))
    return sections


def _extract_docx(path: Path) -> list[TextSection]:
    document = Document(str(path))
    sections: list[TextSection] = []
    for index, paragraph in enumerate(document.paragraphs, start=1):
        if paragraph.text:
            sections.append(TextSection(kind="DOCX", location=f"Paragraph {index}", text=paragraph.text))
    return sections


def _extract_xlsx(path: Path) -> list[TextSection]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    sections: list[TextSection] = []
    try:
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value is not None:
                        sections.append(
                            TextSection(
                                kind="XLSX",
                                location=f"{sheet.title}!{cell.coordinate}",
                                text=str(cell.value),
                            )
                        )
    finally:
        workbook.close()
    return sections


def _search_sections(path: Path, sections: list[TextSection], query_normalized: str) -> list[SearchResult]:
    matches: list[SearchResult] = []
    for section in sections:
        if query_normalized in section.text.lower():
            matches.append(
                SearchResult(
                    source=path,
                    kind=section.kind,
                    location=section.location,
                    snippet=_snippet(section.text, query_normalized),
                    status="matched",
                )
            )
    return matches


def _search_ocr(path: Path, query_normalized: str, executable: str | None, runner) -> list[SearchResult]:
    if not executable:
        return [
            SearchResult(
                source=path,
                kind="OCR",
                location="-",
                snippet="",
                status="skipped",
                message="OCR is not installed.",
            )
        ]
    try:
        text = run_tesseract_ocr(path, executable=executable, runner=runner)
    except OSError as exc:
        return [
            SearchResult(
                source=path,
                kind="OCR",
                location="-",
                snippet="",
                status="failed",
                message=str(exc),
            )
        ]
    if query_normalized not in text.lower():
        return [
            SearchResult(
                source=path,
                kind="OCR",
                location="OCR",
                snippet="",
                status="no_match",
            )
        ]
    return [
        SearchResult(
            source=path,
            kind="OCR",
            location="OCR",
            snippet=_snippet(text, query_normalized),
            status="matched",
        )
    ]


def _snippet(text: str, query_normalized: str) -> str:
    normalized = text.lower()
    index = normalized.find(query_normalized)
    if index < 0:
        return text.strip()[:120]
    start = max(index - 40, 0)
    end = min(index + len(query_normalized) + 40, len(text))
    return " ".join(text[start:end].strip().split())


def _kind_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return "Text"
    if suffix in PDF_SUFFIXES:
        return "PDF"
    if suffix in DOCX_SUFFIXES:
        return "DOCX"
    if suffix in XLSX_SUFFIXES:
        return "XLSX"
    if suffix in IMAGE_SUFFIXES:
        return "Image"
    return "Unknown"
