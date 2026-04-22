from pathlib import Path

from file_compressor.engine import compress_file, compress_many
from file_compressor.models import JobStatus


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_unsupported_file_is_skipped():
    workdir = case_dir("engine-unsupported")
    source = workdir / "notes.txt"
    source.write_text("hello")

    result = compress_file(source)

    assert result.status is JobStatus.SKIPPED
    assert "Unsupported" in result.message


def test_batch_continues_after_failed_file():
    workdir = case_dir("engine-batch")
    bad = workdir / "missing.xlsx"
    unsupported = workdir / "notes.txt"
    unsupported.write_text("hello")

    results = list(compress_many([bad, unsupported]))

    assert [result.status for result in results] == [JobStatus.FAILED, JobStatus.SKIPPED]
