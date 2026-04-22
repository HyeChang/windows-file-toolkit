from pathlib import Path

from file_compressor.models import CompressionResult, JobStatus
from file_compressor_app.view_model import FileJob, result_to_job


def test_file_job_displays_size_in_kb():
    job = FileJob(path=Path("report.pdf"), original_size=1536)

    assert job.original_size_text == "1.5 KB"


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
