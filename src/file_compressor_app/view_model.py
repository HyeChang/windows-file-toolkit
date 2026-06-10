from dataclasses import dataclass
from pathlib import Path

from file_compressor.models import CompressionJob, CompressionResult, JobStatus


def format_size(size: int | None) -> str:
    if size is None:
        return "-"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


@dataclass
class FileJob:
    path: Path
    status: str = JobStatus.PENDING.value
    original_size: int | None = None
    compressed_size: int | None = None
    output_path: Path | None = None
    compression_job: CompressionJob | None = None
    message: str = ""

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def kind(self) -> str:
        return self.path.suffix.lower().lstrip(".") or "-"

    @property
    def original_size_text(self) -> str:
        return format_size(self.original_size)

    @property
    def compressed_size_text(self) -> str:
        return format_size(self.compressed_size)

    @property
    def savings_size(self) -> int | None:
        if self.original_size is None or self.compressed_size is None:
            return None
        return self.original_size - self.compressed_size

    @property
    def savings_rate(self) -> float | None:
        if self.original_size in (None, 0) or self.compressed_size is None:
            return None
        return (self.savings_size or 0) / self.original_size * 100

    @property
    def savings_size_text(self) -> str:
        return format_size(self.savings_size)

    @property
    def savings_rate_text(self) -> str:
        if self.savings_rate is None:
            return "-"
        return f"{self.savings_rate:.1f}%"

    @property
    def output_text(self) -> str:
        return str(self.output_path) if self.output_path else "-"


@dataclass(frozen=True)
class CompressionSummary:
    total: int
    completed: int
    not_needed: int
    skipped: int
    failed: int
    original_size: int | None
    compressed_size: int | None

    @property
    def savings_size(self) -> int | None:
        if self.original_size is None or self.compressed_size is None:
            return None
        return self.original_size - self.compressed_size

    @property
    def savings_rate(self) -> float | None:
        if self.original_size in (None, 0) or self.compressed_size is None:
            return None
        return (self.savings_size or 0) / self.original_size * 100

    @property
    def savings_size_text(self) -> str:
        return format_size(self.savings_size)

    @property
    def savings_rate_text(self) -> str:
        if self.savings_rate is None:
            return "-"
        return f"{self.savings_rate:.1f}%"


def summarize_jobs(jobs: list[FileJob]) -> CompressionSummary:
    completed_jobs = [
        job
        for job in jobs
        if job.status == JobStatus.COMPLETED.value
        and job.original_size is not None
        and job.compressed_size is not None
    ]
    original_size = sum(job.original_size or 0 for job in completed_jobs) if completed_jobs else None
    compressed_size = sum(job.compressed_size or 0 for job in completed_jobs) if completed_jobs else None
    return CompressionSummary(
        total=len(jobs),
        completed=sum(1 for job in jobs if job.status == JobStatus.COMPLETED.value),
        not_needed=sum(1 for job in jobs if job.status == JobStatus.NOT_NEEDED.value),
        skipped=sum(1 for job in jobs if job.status == JobStatus.SKIPPED.value),
        failed=sum(1 for job in jobs if job.status == JobStatus.FAILED.value),
        original_size=original_size,
        compressed_size=compressed_size,
    )


def result_to_job(
    result: CompressionResult,
    *,
    compression_job: CompressionJob | None = None,
) -> FileJob:
    planned_output = compression_job.output if compression_job else None
    return FileJob(
        path=result.source,
        status=result.status.value,
        original_size=result.original_size,
        compressed_size=result.compressed_size,
        output_path=result.output or planned_output,
        compression_job=compression_job,
        message=result.message,
    )
