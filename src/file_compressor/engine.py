from collections.abc import Iterable, Iterator
from pathlib import Path

from file_compressor.compressors.package import compress_zip_document
from file_compressor.compressors.pdf import compress_pdf
from file_compressor.compressors.windows_automation import compress_hwp, compress_legacy_office
from file_compressor.formats import classify_file
from file_compressor.models import CompressionResult, FileKind, JobStatus
from file_compressor.paths import compressed_output_path


def compress_file(source: Path) -> CompressionResult:
    try:
        if not source.exists():
            return CompressionResult(
                status=JobStatus.FAILED,
                source=source,
                message="Source file does not exist.",
            )

        kind = classify_file(source)
        if kind is FileKind.UNSUPPORTED:
            return CompressionResult(
                status=JobStatus.SKIPPED,
                source=source,
                original_size=source.stat().st_size,
                message="Unsupported file type.",
            )

        output = compressed_output_path(source)
        if kind in {FileKind.OOXML, FileKind.HWPX}:
            return compress_zip_document(source, output)
        if kind is FileKind.PDF:
            return compress_pdf(source, output)
        if kind is FileKind.HWP:
            return compress_hwp(source, output)
        if kind is FileKind.LEGACY_OFFICE:
            return compress_legacy_office(source, output)

        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            message="Unsupported file type.",
        )
    except Exception as exc:
        return CompressionResult(status=JobStatus.FAILED, source=source, message=str(exc))


def compress_many(paths: Iterable[Path]) -> Iterator[CompressionResult]:
    for path in paths:
        yield compress_file(path)
