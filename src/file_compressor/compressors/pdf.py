from pathlib import Path
import subprocess

from file_compressor.dependencies import DependencyStatus, detect_ghostscript
from file_compressor.models import CompressionOptions, CompressionResult, JobStatus


PDF_PRESETS = {
    "screen": "screen",
    "ebook": "ebook",
    "printer": "printer",
    "prepress": "prepress",
}


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


def build_ghostscript_command(
    executable: str,
    source: Path,
    output: Path,
    *,
    pdf_preset: str = "screen",
) -> list[str]:
    preset = PDF_PRESETS.get(pdf_preset, "screen")
    return [
        executable,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{preset}",
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
    options: CompressionOptions | None = None,
) -> CompressionResult:
    dependency = dependency or detect_ghostscript()
    options = options or CompressionOptions()
    original_size = source.stat().st_size
    if not dependency.available or dependency.executable is None:
        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            original_size=original_size,
            message="Ghostscript is required for PDF compression.",
        )

    temporary = _temporary_output_path(output)
    command = build_ghostscript_command(
        dependency.executable,
        source,
        temporary,
        pdf_preset=options.pdf_preset,
    )
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
