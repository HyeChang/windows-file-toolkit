from pathlib import Path
import shutil

from file_compressor.paths import compressed_output_path


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def test_compressed_output_path_adds_suffix_next_to_source():
    workdir = case_dir("path-basic")
    source = workdir / "report.pdf"
    source.write_bytes(b"source")

    result = compressed_output_path(source)

    assert result == workdir / "report_compressed.pdf"


def test_compressed_output_path_uses_number_when_target_exists():
    workdir = case_dir("path-collision")
    source = workdir / "report.pdf"
    source.write_bytes(b"source")
    (workdir / "report_compressed.pdf").write_bytes(b"existing")
    (workdir / "report_compressed_2.pdf").write_bytes(b"existing")

    result = compressed_output_path(source)

    assert result == workdir / "report_compressed_3.pdf"
