from collections.abc import Iterable, Iterator
from pathlib import Path

from file_compressor.compressors.package import compress_zip_document
from file_compressor.compressors.pdf import compress_pdf
from file_compressor.compressors.windows_automation import compress_hwp, compress_legacy_office
from file_compressor.discovery import expand_source_paths
from file_compressor.formats import classify_file
from file_compressor.models import CompressionJob, CompressionOptions, CompressionResult, FileKind, JobStatus
from file_compressor.paths import compressed_output_path
from file_compressor.planning import LEGACY_OUTPUT_SUFFIXES


def expand_sources(paths: Iterable[Path]) -> list[Path]:
    return expand_source_paths(paths)


def _default_output_path(source: Path) -> Path:
    suffix = LEGACY_OUTPUT_SUFFIXES.get(source.suffix.lower())
    if suffix is None:
        return compressed_output_path(source)
    return compressed_output_path(source.with_suffix(suffix))


def _compress_to_output(
    source: Path,
    output: Path,
    options: CompressionOptions,
) -> CompressionResult:
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

    output.parent.mkdir(parents=True, exist_ok=True)

    if kind in {FileKind.OOXML, FileKind.HWPX}:
        return compress_zip_document(source, output, options=options)
    if kind is FileKind.PDF:
        return compress_pdf(source, output, options=options)
    if kind is FileKind.HWP:
        return compress_hwp(source, output, options=options)
    if kind is FileKind.LEGACY_OFFICE:
        return compress_legacy_office(source, output, options=options)

    return CompressionResult(
        status=JobStatus.SKIPPED,
        source=source,
        message="Unsupported file type.",
    )


def compress_job(
    job: CompressionJob,
    options: CompressionOptions | None = None,
) -> CompressionResult:
    options = options or CompressionOptions()
    try:
        return _compress_to_output(job.source, job.output, options)
    except Exception as exc:
        return CompressionResult(status=JobStatus.FAILED, source=job.source, message=str(exc))


def compress_file(
    source: Path | CompressionJob,
    options: CompressionOptions | None = None,
) -> CompressionResult:
    if isinstance(source, CompressionJob):
        return compress_job(source, options)

    options = options or CompressionOptions()
    try:
        return _compress_to_output(source, _default_output_path(source), options)
    except Exception as exc:
        return CompressionResult(status=JobStatus.FAILED, source=source, message=str(exc))


def compress_many(
    paths: Iterable[Path | CompressionJob],
    *,
    options: CompressionOptions | None = None,
) -> Iterator[CompressionResult]:
    options = options or CompressionOptions()
    for path in paths:
        yield compress_file(path, options)
