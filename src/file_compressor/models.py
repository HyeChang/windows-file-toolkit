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
class CompressionOptions:
    max_image_dimension: int | None = 1600
    jpeg_quality: int = 78
    pdf_preset: str = "screen"


@dataclass(frozen=True)
class CompressionResult:
    status: JobStatus
    source: Path
    output: Path | None = None
    original_size: int | None = None
    compressed_size: int | None = None
    message: str = ""
