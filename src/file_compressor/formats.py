from pathlib import Path

from file_compressor.models import FileKind


OOXML_EXTENSIONS = {".xlsx", ".xlsm", ".pptx", ".pptm"}
LEGACY_OFFICE_EXTENSIONS = {".xls", ".ppt"}


def classify_file(path: Path) -> FileKind:
    suffix = path.suffix.lower()
    if suffix in OOXML_EXTENSIONS:
        return FileKind.OOXML
    if suffix == ".hwpx":
        return FileKind.HWPX
    if suffix == ".pdf":
        return FileKind.PDF
    if suffix == ".hwp":
        return FileKind.HWP
    if suffix in LEGACY_OFFICE_EXTENSIONS:
        return FileKind.LEGACY_OFFICE
    return FileKind.UNSUPPORTED
