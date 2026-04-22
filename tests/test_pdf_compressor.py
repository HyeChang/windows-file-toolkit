from pathlib import Path

from file_compressor.compressors.pdf import build_ghostscript_command, compress_pdf
from file_compressor.dependencies import DependencyStatus
from file_compressor.models import JobStatus


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_build_ghostscript_command_uses_screen_setting():
    workdir = case_dir("pdf-command")
    source = workdir / "input.pdf"
    output = workdir / "output.pdf"

    command = build_ghostscript_command("gs", source, output)

    assert command[0] == "gs"
    assert "-sDEVICE=pdfwrite" in command
    assert "-dPDFSETTINGS=/screen" in command
    assert f"-sOutputFile={output}" in command
    assert str(source) == command[-1]


def test_compress_pdf_skips_when_ghostscript_missing():
    workdir = case_dir("pdf-missing-gs")
    source = workdir / "input.pdf"
    source.write_bytes(b"%PDF-1.4")
    output = workdir / "output.pdf"

    result = compress_pdf(source, output, dependency=DependencyStatus(False))

    assert result.status is JobStatus.SKIPPED
    assert result.output is None
    assert "Ghostscript" in result.message
