from dataclasses import dataclass
from pathlib import Path

from file_compressor.models import CompressionResult, JobStatus


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
    def output_text(self) -> str:
        return str(self.output_path) if self.output_path else "-"


def result_to_job(result: CompressionResult) -> FileJob:
    return FileJob(
        path=result.source,
        status=result.status.value,
        original_size=result.original_size,
        compressed_size=result.compressed_size,
        output_path=result.output,
        message=result.message,
    )
