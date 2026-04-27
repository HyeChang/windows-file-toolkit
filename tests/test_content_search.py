from pathlib import Path
import shutil

from docx import Document
from openpyxl import Workbook
from reportlab.pdfgen import canvas

from file_compressor.content_search import (
    SearchResult,
    extract_text_from_file,
    run_tesseract_ocr,
    search_files,
)
from file_compressor.dependencies import TESSERACT_DOWNLOAD_URL, detect_tesseract


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def write_text_pdf(path: Path, text: str):
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, text)
    pdf.save()


def test_extract_text_from_supported_file_types():
    workdir = case_dir("content-extract")
    text_file = workdir / "memo.txt"
    pdf_file = workdir / "report.pdf"
    docx_file = workdir / "letter.docx"
    xlsx_file = workdir / "sheet.xlsx"
    text_file.write_text("alpha text", encoding="utf-8")
    write_text_pdf(pdf_file, "bravo pdf text")
    document = Document()
    document.add_paragraph("charlie docx text")
    document.save(docx_file)
    workbook = Workbook()
    workbook.active["A1"] = "delta xlsx text"
    workbook.save(xlsx_file)

    assert "alpha text" in "\n".join(section.text for section in extract_text_from_file(text_file))
    assert "bravo pdf text" in "\n".join(section.text for section in extract_text_from_file(pdf_file))
    assert "charlie docx text" in "\n".join(section.text for section in extract_text_from_file(docx_file))
    assert "delta xlsx text" in "\n".join(section.text for section in extract_text_from_file(xlsx_file))


def test_search_files_reports_matches_with_locations_and_snippets():
    workdir = case_dir("content-search")
    source = workdir / "memo.txt"
    source.write_text("first line\nneedle appears here\nlast line", encoding="utf-8")

    results = search_files([source], "needle")

    assert results == [
        SearchResult(
            source=source,
            kind="Text",
            location="Line 2",
            snippet="needle appears here",
            status="matched",
        )
    ]


def test_search_files_reports_no_match_and_unsupported_files():
    workdir = case_dir("content-no-match")
    text_file = workdir / "memo.txt"
    binary_file = workdir / "app.bin"
    text_file.write_text("nothing useful", encoding="utf-8")
    binary_file.write_bytes(b"\x00\x01")

    results = search_files([text_file, binary_file], "needle")

    assert results[0].status == "no_match"
    assert results[1].status == "skipped"
    assert results[1].message == "Unsupported file type."


def test_detect_tesseract_and_download_url():
    assert detect_tesseract(lambda name: "C:/Tools/tesseract.exe" if name == "tesseract" else None).available is True
    assert detect_tesseract(lambda name: None).available is False
    assert TESSERACT_DOWNLOAD_URL == "https://github.com/UB-Mannheim/tesseract/wiki"


def test_run_tesseract_ocr_uses_runner_and_search_can_use_ocr_fallback():
    workdir = case_dir("content-ocr")
    image = workdir / "scan.png"
    image.write_bytes(b"fake image")
    calls = []

    def fake_runner(command, **kwargs):
        calls.append((command, kwargs))

        class Result:
            stdout = "needle from ocr"
            stderr = ""
            returncode = 0

        return Result()

    assert run_tesseract_ocr(image, executable="tesseract", runner=fake_runner) == "needle from ocr"

    results = search_files(
        [image],
        "needle",
        use_ocr=True,
        tesseract_executable="tesseract",
        ocr_runner=fake_runner,
    )

    assert calls[0][0] == ["tesseract", str(image), "stdout", "-l", "kor+eng"]
    assert results[0].status == "matched"
    assert results[0].location == "OCR"
