from collections.abc import Callable
from pathlib import Path
from typing import Any

from file_compressor.models import CompressionResult, JobStatus


def _source_size(source: Path) -> int | None:
    return source.stat().st_size if source.exists() else None


def is_progid_registered(
    progid: str,
    *,
    open_key: Callable[[Any, str], Any] | None = None,
) -> bool:
    try:
        import winreg

        key_root = winreg.HKEY_CLASSES_ROOT
        key_open = open_key or winreg.OpenKey
    except ImportError:
        key_root = None
        if open_key is None:
            return False
        key_open = open_key

    try:
        with key_open(key_root, f"{progid}\\CLSID"):
            return True
    except OSError:
        return False


def default_hancom_available() -> bool:
    return is_progid_registered("HWPFrame.HwpObject")


def default_office_available() -> bool:
    return is_progid_registered("Excel.Application")


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
