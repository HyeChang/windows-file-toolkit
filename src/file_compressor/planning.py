from pathlib import Path

from file_compressor.models import CompressionJob
from file_compressor.paths import compressed_output_path


LEGACY_OUTPUT_SUFFIXES = {
    ".xls": ".xlsx",
    ".ppt": ".pptx",
}


def folder_batch_output_root(source_root: Path) -> Path:
    base = source_root.with_name(f"{source_root.name}_압축됨")
    if not base.exists():
        return base

    counter = 2
    while True:
        candidate = source_root.with_name(f"{source_root.name}_압축됨_{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def planned_batch_output_path(
    source: Path,
    source_root: Path,
    *,
    batch_root: Path | None = None,
) -> Path:
    batch_root = batch_root or folder_batch_output_root(source_root)
    relative_path = source.relative_to(source_root)
    suffix = LEGACY_OUTPUT_SUFFIXES.get(source.suffix.lower(), source.suffix)
    return batch_root / relative_path.with_suffix(suffix)


def planned_output_folder_path(
    source: Path,
    output_root: Path,
    *,
    source_root: Path | None = None,
) -> Path:
    suffix = LEGACY_OUTPUT_SUFFIXES.get(source.suffix.lower(), source.suffix)
    if source_root is not None:
        relative_path = source.relative_to(source_root)
        return output_root / relative_path.with_suffix(suffix)

    converted_source = source.with_suffix(suffix)
    return output_root / compressed_output_path(converted_source).name


def plan_folder_job(source: Path, source_root: Path) -> CompressionJob:
    batch_root = folder_batch_output_root(source_root)
    return CompressionJob(
        source=source,
        output=planned_batch_output_path(source, source_root, batch_root=batch_root),
        batch_root=batch_root,
    )
