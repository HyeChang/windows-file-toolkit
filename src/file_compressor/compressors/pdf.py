from pathlib import Path
import subprocess

from file_compressor.dependencies import DependencyStatus, detect_ghostscript
from file_compressor.models import CompressionResult, JobStatus


def _temporary_output_path(output: Path) -> Path:
    candidate = output.with_name(f"{output.name}.tmp")
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = output.with_name(f"{output.name}.{counter}.tmp")
        if not candidate.exists():
            return candidate
        counter += 1


def build_ghostscript_command(executable: str, source: Path, output: Path) -> list[str]:
    return [
        executable,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/screen",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output}",
        str(source),
    ]


def compress_pdf(
    source: Path,
    output: Path,
    *,
    dependency: DependencyStatus | None = None,
) -> CompressionResult:
    dependency = dependency or detect_ghostscript()
    original_size = source.stat().st_size
    if not dependency.available or dependency.executable is None:
        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            original_size=original_size,
            message="Ghostscript is required for PDF compression.",
        )

    temporary = _temporary_output_path(output)
    command = build_ghostscript_command(dependency.executable, source, temporary)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0 or not temporary.exists():
        if temporary.exists():
            temporary.unlink()
        return CompressionResult(
            status=JobStatus.FAILED,
            source=source,
            original_size=original_size,
            message=completed.stderr.strip() or "Ghostscript failed.",
        )

    try:
        temporary.replace(output)
    except OSError as exc:
        if temporary.exists():
            temporary.unlink()
        return CompressionResult(
            status=JobStatus.FAILED,
            source=source,
            original_size=original_size,
            message=str(exc),
        )

    return CompressionResult(
        status=JobStatus.COMPLETED,
        source=source,
        output=output,
        original_size=original_size,
        compressed_size=output.stat().st_size,
        message="Compressed",
    )
