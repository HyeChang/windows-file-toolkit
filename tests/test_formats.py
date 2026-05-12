from pathlib import Path

from file_compressor.formats import classify_file
from file_compressor.models import FileKind, JobStatus


def test_classifies_zip_based_office_files_case_insensitively():
    assert classify_file(Path("book.XLSX")) is FileKind.OOXML
    assert classify_file(Path("deck.pptm")) is FileKind.OOXML
    assert classify_file(Path("letter.DOCX")) is FileKind.OOXML


def test_classifies_korean_and_pdf_files():
    assert classify_file(Path("doc.hwpx")) is FileKind.HWPX
    assert classify_file(Path("doc.hwp")) is FileKind.HWP
    assert classify_file(Path("doc.pdf")) is FileKind.PDF


def test_classifies_legacy_office_and_unsupported_files():
    assert classify_file(Path("legacy.xls")) is FileKind.LEGACY_OFFICE
    assert classify_file(Path("notes.txt")) is FileKind.UNSUPPORTED


def test_job_status_values_are_stable_for_ui():
    assert [status.value for status in JobStatus] == [
        "pending",
        "processing",
        "completed",
        "skipped",
        "failed",
    ]
