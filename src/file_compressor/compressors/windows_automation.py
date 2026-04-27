from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

from file_compressor.compressors.package import compress_zip_document
from file_compressor.models import CompressionOptions, CompressionResult, JobStatus


EXCEL_APPLICATION_PROGID = "Excel.Application"
POWERPOINT_APPLICATION_PROGID = "PowerPoint.Application"
EXCEL_XLSX_FILE_FORMAT = 51
POWERPOINT_PPTX_FILE_FORMAT = 24


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


def default_excel_available() -> bool:
    return is_progid_registered(EXCEL_APPLICATION_PROGID)


def default_powerpoint_available() -> bool:
    return is_progid_registered(POWERPOINT_APPLICATION_PROGID)


def default_office_available() -> bool:
    return default_excel_available() or default_powerpoint_available()


def default_com_dispatch(progid: str) -> Any:
    import win32com.client

    return win32com.client.DispatchEx(progid)


def _initialize_com() -> Callable[[], None]:
    try:
        import pythoncom
    except ImportError:
        return lambda: None

    pythoncom.CoInitialize()
    return pythoncom.CoUninitialize


def compress_hwp(
    source: Path,
    output: Path,
    *,
    options: CompressionOptions | None = None,
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
    options: CompressionOptions | None = None,
    automation_available: Callable[[], bool] | None = None,
    dispatch: Callable[[str], Any] = default_com_dispatch,
) -> CompressionResult:
    options = options or CompressionOptions()
    automation = _legacy_office_automation(source)
    if automation is None:
        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            original_size=_source_size(source),
            message="Unsupported legacy Office file type.",
        )

    progid, output_suffix, default_available, convert = automation
    available = automation_available or default_available
    if not available():
        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            original_size=_source_size(source),
            message="Microsoft Office is required for legacy Office compression.",
        )

    original_size = _source_size(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    uninitialize = _initialize_com()
    converted = output.with_name(f"{output.stem}.conversion-{uuid4().hex}{output_suffix}")
    try:
        app = dispatch(progid)
        convert(app, source, converted)
        zip_result = compress_zip_document(converted, output, options=options)
        return CompressionResult(
            status=zip_result.status,
            source=source,
            output=zip_result.output,
            original_size=original_size,
            compressed_size=zip_result.compressed_size,
            message=zip_result.message,
        )
    except Exception as exc:
        return CompressionResult(
            status=JobStatus.FAILED,
            source=source,
            original_size=original_size,
            message=str(exc),
        )
    finally:
        _remove_file_if_exists(converted)
        uninitialize()


def _legacy_office_automation(
    source: Path,
) -> tuple[str, str, Callable[[], bool], Callable[[Any, Path, Path], None]] | None:
    suffix = source.suffix.lower()
    if suffix == ".xls":
        return (
            EXCEL_APPLICATION_PROGID,
            ".xlsx",
            default_excel_available,
            _convert_excel_to_xlsx,
        )
    if suffix == ".ppt":
        return (
            POWERPOINT_APPLICATION_PROGID,
            ".pptx",
            default_powerpoint_available,
            _convert_powerpoint_to_pptx,
        )
    return None


def _convert_excel_to_xlsx(app: Any, source: Path, output: Path) -> None:
    workbook = None
    try:
        app.DisplayAlerts = False
        workbook = app.Workbooks.Open(str(source.resolve()))
        workbook.SaveAs(str(output.resolve()), FileFormat=EXCEL_XLSX_FILE_FORMAT)
    finally:
        try:
            if workbook is not None:
                workbook.Close(SaveChanges=False)
        finally:
            app.Quit()


def _convert_powerpoint_to_pptx(app: Any, source: Path, output: Path) -> None:
    presentation = None
    try:
        presentation = app.Presentations.Open(str(source.resolve()), WithWindow=False)
        presentation.SaveAs(str(output.resolve()), POWERPOINT_PPTX_FILE_FORMAT)
    finally:
        try:
            if presentation is not None:
                presentation.Close()
        finally:
            app.Quit()


def _remove_file_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
