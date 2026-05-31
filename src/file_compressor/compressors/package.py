from pathlib import Path

from file_compressor.images import optimize_image_bytes
from file_compressor.models import CompressionOptions, CompressionResult, JobStatus
from file_compressor.zip_packages import rewrite_zip_package


CONTENT_TYPES_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def compress_zip_document(
    source: Path,
    output: Path,
    *,
    options: CompressionOptions | None = None,
) -> CompressionResult:
    options = options or CompressionOptions()
    original_size = source.stat().st_size

    def transform(name: str, data: bytes) -> bytes:
        suffix = Path(name).suffix.lower()
        content_type = CONTENT_TYPES_BY_EXTENSION.get(suffix)
        if content_type is None:
            return data
        return optimize_image_bytes(
            content_type,
            data,
            max_dimension=options.max_image_dimension,
            jpeg_quality=options.jpeg_quality,
        )

    rewrite_zip_package(source, output, transform)
    return CompressionResult(
        status=JobStatus.COMPLETED,
        source=source,
        output=output,
        original_size=original_size,
        compressed_size=output.stat().st_size,
        message="Compressed",
    )
