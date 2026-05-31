from pathlib import Path

from file_compressor.models import CompressionJob, CompressionResult, JobStatus
from file_compressor_app.view_model import FileJob, summarize_jobs, result_to_job


def test_file_job_displays_size_in_kb():
    job = FileJob(path=Path("report.pdf"), original_size=1536)

    assert job.original_size_text == "1.5 KB"


def test_file_job_displays_savings_amount_and_rate():
    job = FileJob(
        path=Path("report.pdf"),
        original_size=2000,
        compressed_size=1000,
    )

    assert job.savings_size_text == "1000 B"
    assert job.savings_rate_text == "50.0%"


def test_file_job_hides_savings_when_job_was_skipped_with_output_copy():
    job = FileJob(
        path=Path("report.hwp"),
        status=JobStatus.SKIPPED.value,
        original_size=2000,
        compressed_size=None,
        output_path=Path("report_compressed.hwp"),
        message="copied original",
    )

    assert job.compressed_size_text == "-"
    assert job.savings_size_text == "-"
    assert job.savings_rate_text == "-"
    assert job.output_text == "report_compressed.hwp"


def test_result_to_job_copies_output_and_status():
    result = CompressionResult(
        status=JobStatus.COMPLETED,
        source=Path("report.pdf"),
        output=Path("report_compressed.pdf"),
        original_size=2000,
        compressed_size=1000,
        message="Compressed",
    )

    job = result_to_job(result)

    assert job.status == "completed"
    assert job.output_path == Path("report_compressed.pdf")
    assert job.compressed_size_text == "1000 B"


def test_result_to_job_preserves_planned_output_when_result_has_no_output():
    planned = CompressionJob(
        source=Path("folder/report.xlsx"),
        output=Path("folder_압축됨/report.xlsx"),
    )
    result = CompressionResult(
        status=JobStatus.FAILED,
        source=planned.source,
        original_size=2000,
        message="failed",
    )

    job = result_to_job(result, compression_job=planned)

    assert job.compression_job == planned
    assert job.output_path == planned.output


def test_summarize_jobs_counts_statuses_and_total_savings():
    jobs = [
        FileJob(
            path=Path("done.pdf"),
            status="completed",
            original_size=2000,
            compressed_size=1000,
        ),
        FileJob(path=Path("not-needed.pdf"), status="not_needed", original_size=300),
        FileJob(path=Path("skipped.pdf"), status="skipped", original_size=500),
        FileJob(path=Path("failed.pdf"), status="failed", original_size=700),
    ]

    summary = summarize_jobs(jobs)

    assert summary.total == 4
    assert summary.completed == 1
    assert summary.not_needed == 1
    assert summary.skipped == 1
    assert summary.failed == 1
    assert summary.original_size == 2000
    assert summary.compressed_size == 1000
    assert summary.savings_size_text == "1000 B"
    assert summary.savings_rate_text == "50.0%"
