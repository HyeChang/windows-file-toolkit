from pathlib import Path

from file_compressor.engine import compress_file, compress_job, compress_many
from file_compressor.models import CompressionJob, CompressionOptions, CompressionResult, JobStatus


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


def test_batch_passes_options_to_each_file(monkeypatch):
    workdir = case_dir("engine-options")
    source = workdir / "notes.txt"
    source.write_text("hello")
    options = CompressionOptions(jpeg_quality=50)
    calls = []

    def fake_compress_file(path, selected_options):
        calls.append((path, selected_options))
        return None

    monkeypatch.setattr("file_compressor.engine.compress_file", fake_compress_file)

    list(compress_many([source], options=options))

    assert calls == [(source, options)]


def test_compress_job_uses_explicit_output_and_creates_parent(monkeypatch):
    workdir = case_dir("engine-job-output")
    source = workdir / "report.xlsx"
    source.write_text("xlsx")
    output = workdir / "planned" / "nested" / "report.xlsx"
    options = CompressionOptions(jpeg_quality=60)
    calls = []

    def fake_compress_zip_document(path, selected_output, *, options=None):
        calls.append((path, selected_output, options, selected_output.parent.exists()))
        return CompressionResult(
            status=JobStatus.COMPLETED,
            source=path,
            output=selected_output,
            message="Compressed",
        )

    monkeypatch.setattr("file_compressor.engine.compress_zip_document", fake_compress_zip_document)

    result = compress_job(CompressionJob(source=source, output=output), options=options)

    assert result.output == output
    assert calls == [(source, output, options, True)]


def test_compress_many_accepts_paths_and_jobs(monkeypatch):
    workdir = case_dir("engine-many-jobs")
    path_source = workdir / "path.xlsx"
    path_source.write_text("xlsx")
    job_source = workdir / "job.xlsx"
    job_source.write_text("xlsx")
    job = CompressionJob(source=job_source, output=workdir / "out" / "job.xlsx")
    options = CompressionOptions(jpeg_quality=55)
    calls = []

    def fake_compress_zip_document(path, output, *, options=None):
        calls.append((path, output, options))
        return CompressionResult(status=JobStatus.COMPLETED, source=path, output=output)

    monkeypatch.setattr("file_compressor.engine.compress_zip_document", fake_compress_zip_document)

    list(compress_many([path_source, job], options=options))

    assert calls[0][0] == path_source
    assert calls[0][1].suffix == ".xlsx"
    assert calls[0][2] is options
    assert calls[1] == (job_source, job.output, options)


def test_docx_path_input_is_compressed_as_ooxml(monkeypatch):
    workdir = case_dir("engine-docx")
    source = workdir / "letter.docx"
    source.write_text("docx")
    calls = []

    def fake_compress_zip_document(path, output, *, options=None):
        calls.append((path, output))
        return CompressionResult(status=JobStatus.COMPLETED, source=path, output=output)

    monkeypatch.setattr("file_compressor.engine.compress_zip_document", fake_compress_zip_document)

    result = compress_file(source)

    assert result.status is JobStatus.COMPLETED
    assert result.output == workdir / "letter_compressed.docx"
    assert calls == [(source, workdir / "letter_compressed.docx")]


def test_legacy_path_input_uses_modern_output_suffix(monkeypatch):
    workdir = case_dir("engine-legacy-path-output")
    source = workdir / "budget.xls"
    source.write_text("xls")
    calls = []

    def fake_compress_legacy_office(path, output, *, options=None):
        calls.append((path, output))
        return CompressionResult(status=JobStatus.COMPLETED, source=path, output=output)

    monkeypatch.setattr("file_compressor.engine.compress_legacy_office", fake_compress_legacy_office)

    result = compress_file(source)

    assert result.output == workdir / "budget_compressed.xlsx"
    assert calls == [(source, workdir / "budget_compressed.xlsx")]


def test_missing_and_unsupported_jobs_do_not_crash():
    workdir = case_dir("engine-job-errors")
    missing = CompressionJob(
        source=workdir / "missing.xlsx",
        output=workdir / "out" / "missing.xlsx",
    )
    unsupported_source = workdir / "notes.txt"
    unsupported_source.write_text("hello")
    unsupported = CompressionJob(
        source=unsupported_source,
        output=workdir / "out" / "notes.txt",
    )

    results = list(compress_many([missing, unsupported]))

    assert [result.status for result in results] == [JobStatus.FAILED, JobStatus.SKIPPED]
    assert [result.source for result in results] == [missing.source, unsupported.source]
