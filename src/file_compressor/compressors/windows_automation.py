from collections.abc import Callable
from pathlib import Path

from file_compressor.models import CompressionResult, JobStatus


def _source_size(source: Path) -> int | None:
    return source.stat().st_size if source.exists() else None


def default_hancom_available() -> bool:
    try:
        import win32com.client  # type: ignore

        win32com.client.Dispatch("HWPFrame.HwpObject")
        return True
    except Exception:
        return False


def default_office_available() -> bool:
    try:
        import win32com.client  # type: ignore

        win32com.client.Dispatch("Excel.Application")
        return True
    except Exception:
        return False


def compress_hwp(
    source: Path,
    output: Path,
    *,
    automation_available: Callable[[], bool] = default_hancom_available,
) -> CompressionResult:
    if not automation_available():
        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            original_size=_source_size(source),
            message="Hancom Office is required for HWP compression.",
        )

    return CompressionResult(
        status=JobStatus.SKIPPED,
        source=source,
        original_size=_source_size(source),
        message="HWP automation is detected but compression flow is not implemented in this version.",
    )


def compress_legacy_office(
    source: Path,
    output: Path,
    *,
    automation_available: Callable[[], bool] = default_office_available,
) -> CompressionResult:
    if not automation_available():
        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            original_size=_source_size(source),
            message="Microsoft Office is required for legacy Office compression.",
        )

    return CompressionResult(
        status=JobStatus.SKIPPED,
        source=source,
        original_size=_source_size(source),
        message="Legacy Office automation is detected but conversion flow is not implemented in this version.",
    )
