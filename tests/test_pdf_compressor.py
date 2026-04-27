from pathlib import Path
import shutil

from file_compressor.compressors.pdf import build_ghostscript_command, compress_pdf
from file_compressor.dependencies import DependencyStatus
from file_compressor.models import CompressionOptions, JobStatus


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
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


def test_build_ghostscript_command_uses_selected_pdf_preset():
    workdir = case_dir("pdf-command-preset")
    source = workdir / "input.pdf"
    output = workdir / "output.pdf"

    command = build_ghostscript_command("gs", source, output, pdf_preset="ebook")

    assert "-dPDFSETTINGS=/ebook" in command


def test_compress_pdf_skips_when_ghostscript_missing():
    workdir = case_dir("pdf-missing-gs")
    source = workdir / "input.pdf"
    source.write_bytes(b"%PDF-1.4")
    output = workdir / "output.pdf"

    result = compress_pdf(source, output, dependency=DependencyStatus(False))

    assert result.status is JobStatus.SKIPPED
    assert result.output is None
    assert "Ghostscript" in result.message
    assert "Install" in result.message


def test_compress_pdf_removes_partial_output_when_ghostscript_fails(monkeypatch):
    workdir = case_dir("pdf-partial-failure")
    source = workdir / "input.pdf"
    source.write_bytes(b"%PDF-1.4")
    output = workdir / "output.pdf"

    class Completed:
        returncode = 1
        stderr = "failed"

    def fake_run(command, check, capture_output, text):
        partial_output = Path(command[-2].removeprefix("-sOutputFile="))
        partial_output.write_bytes(b"partial")
        return Completed()

    monkeypatch.setattr("file_compressor.compressors.pdf.subprocess.run", fake_run)

    result = compress_pdf(source, output, dependency=DependencyStatus(True, "gs"))

    assert result.status is JobStatus.FAILED
    assert not output.exists()


def test_compress_pdf_removes_temp_output_when_final_replace_fails(monkeypatch):
    workdir = case_dir("pdf-replace-failure")
    source = workdir / "input.pdf"
    source.write_bytes(b"%PDF-1.4")
    output = workdir / "output.pdf"

    class Completed:
        returncode = 0
        stderr = ""

    def fake_run(command, check, capture_output, text):
        temporary_output = Path(command[-2].removeprefix("-sOutputFile="))
        temporary_output.write_bytes(b"compressed")
        return Completed()

    def fail_replace(self, target):
        raise OSError("replace failed")

    monkeypatch.setattr("file_compressor.compressors.pdf.subprocess.run", fake_run)
    monkeypatch.setattr(Path, "replace", fail_replace)

    result = compress_pdf(source, output, dependency=DependencyStatus(True, "gs"))

    assert result.status is JobStatus.FAILED
    assert not output.exists()
    assert not list(workdir.glob("*.tmp"))


def test_compress_pdf_passes_selected_preset_to_ghostscript(monkeypatch):
    workdir = case_dir("pdf-selected-preset")
    source = workdir / "input.pdf"
    source.write_bytes(b"%PDF-1.4")
    output = workdir / "output.pdf"
    commands = []

    class Completed:
        returncode = 1
        stderr = "failed"

    def fake_run(command, check, capture_output, text):
        commands.append(command)
        return Completed()

    monkeypatch.setattr("file_compressor.compressors.pdf.subprocess.run", fake_run)

    compress_pdf(
        source,
        output,
        dependency=DependencyStatus(True, "gs"),
        options=CompressionOptions(pdf_preset="prepress"),
    )

    assert "-dPDFSETTINGS=/prepress" in commands[0]
