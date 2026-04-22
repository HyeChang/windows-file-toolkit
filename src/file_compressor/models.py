from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FileKind(Enum):
    OOXML = "ooxml"
    HWPX = "hwpx"
    PDF = "pdf"
    HWP = "hwp"
    LEGACY_OFFICE = "legacy_office"
    UNSUPPORTED = "unsupported"


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class CompressionResult:
    status: JobStatus
    source: Path
    output: Path | None = None
    original_size: int | None = None
    compressed_size: int | None = None
    message: str = ""
