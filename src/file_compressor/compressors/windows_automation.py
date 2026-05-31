from collections.abc import Callable
import importlib
from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4

from file_compressor.compressors.package import compress_zip_document
from file_compressor.models import CompressionOptions, CompressionResult, JobStatus


EXCEL_APPLICATION_PROGID = "Excel.Application"
HWP_APPLICATION_PROGID = "HWPFrame.HwpObject"
POWERPOINT_APPLICATION_PROGID = "PowerPoint.Application"
EXCEL_XLSX_FILE_FORMAT = 51
POWERPOINT_PPTX_FILE_FORMAT = 24
HWP_FILE_PATH_CHECKER_MODULES = ("FilePathCheckerModule", "FilePathCheckerModuleExample")


class HwpSecurityModuleUnavailable(RuntimeError):
    pass


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


def is_pywin32_available(
    *,
    import_module: Callable[[str], Any] = importlib.import_module,
) -> bool:
    try:
        import_module("win32com.client")
    except ImportError:
        return False
    return True


def default_hancom_available(
    *,
    progid_registered: Callable[[], bool] | None = None,
    pywin32_available: Callable[[], bool] = is_pywin32_available,
) -> bool:
    registered = progid_registered or (lambda: is_progid_registered(HWP_APPLICATION_PROGID))
    return registered() and pywin32_available()


def default_excel_available() -> bool:
    return is_progid_registered(EXCEL_APPLICATION_PROGID)


def default_powerpoint_available() -> bool:
    return is_progid_registered(POWERPOINT_APPLICATION_PROGID)


def default_office_available() -> bool:
    return default_excel_available() or default_powerpoint_available()


def default_com_dispatch(progid: str) -> Any:
    try:
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("pywin32 is required for Windows Office/Hancom automation.") from exc

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
    dispatch: Callable[[str], Any] = default_com_dispatch,
) -> CompressionResult:
    if not automation_available():
        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            original_size=_source_size(source),
            message="Hancom Office is required for HWP compression.",
        )

    original_size = _source_size(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    uninitialize = _initialize_com()
    try:
        app = dispatch(HWP_APPLICATION_PROGID)
        message = _save_hwp_document(app, source, output)
        return CompressionResult(
            status=JobStatus.COMPLETED,
            source=source,
            output=output,
            original_size=original_size,
            compressed_size=output.stat().st_size if output.exists() else None,
            message=message,
        )
    except HwpSecurityModuleUnavailable as exc:
        return _copy_hwp_fallback(source, output, original_size, str(exc))
    except Exception as exc:
        return CompressionResult(
            status=JobStatus.FAILED,
            source=source,
            original_size=original_size,
            message=str(exc),
        )
    finally:
        uninitialize()


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


def _save_hwp_document(app: Any, source: Path, output: Path) -> str:
    try:
        security_module_registered = _register_hwp_file_path_checker(app)
        if not security_module_registered:
            _show_hwp_window_for_manual_approval(app)
        try:
            _open_hwp_document(app, source)
            _save_hwp_as(app, output)
            if not output.exists():
                raise RuntimeError("HWP file was saved but output was not created.")
        except Exception as exc:
            if not security_module_registered:
                raise HwpSecurityModuleUnavailable(
                    "Hancom manual security approval was not completed; copied the original HWP file instead."
                ) from exc
            raise
        if security_module_registered:
            return "Compressed"
        return "Compressed after manual Hancom security approval."
    finally:
        _quit_application(app)


def _register_hwp_file_path_checker(app: Any) -> bool:
    for module_name in HWP_FILE_PATH_CHECKER_MODULES:
        try:
            result = app.RegisterModule("FilePathCheckDLL", module_name)
        except Exception:
            continue
        if result is not False:
            return True
    return False


def _show_hwp_window_for_manual_approval(app: Any) -> None:
    try:
        app.XHwpWindows.Item(0).Visible = True
        return
    except Exception:
        pass

    try:
        app.Visible = True
    except Exception:
        pass


def _open_hwp_document(app: Any, source: Path) -> None:
    target = str(source.resolve())
    _try_hwp_call(
        app.Open,
        [
            (target,),
            (target, "HWP", ""),
            (target, "HWP", "forceopen:true"),
            (target, "HWP", "forceopen:true;versionwarning:false"),
        ],
        "HWP file could not be opened.",
    )


def _save_hwp_as(app: Any, output: Path) -> None:
    target = str(output.resolve())
    errors: list[Exception] = []
    for args in [(target, "HWP"), (target, "HWP", ""), (target,)]:
        try:
            result = app.SaveAs(*args)
        except Exception as exc:
            errors.append(exc)
            continue
        if output.exists():
            return
        if result is False:
            errors.append(RuntimeError("SaveAs returned False."))
            continue
        errors.append(RuntimeError("SaveAs returned without creating output."))

    _save_hwp_as_action(app, target, output, errors)
    if output.exists():
        return

    if errors:
        raise RuntimeError(f"HWP file could not be saved. {errors[0]}")
    raise RuntimeError("HWP file could not be saved.")


def _save_hwp_as_action(app: Any, target: str, output: Path, errors: list[Exception]) -> None:
    try:
        file_open_save = app.HParameterSet.HFileOpenSave
        hset = file_open_save.HSet
        app.HAction.GetDefault("FileSaveAs_S", hset)
        file_open_save.filename = target
        file_open_save.FileName = target
        file_open_save.Format = "HWP"
        result = app.HAction.Execute("FileSaveAs_S", hset)
    except Exception as exc:
        errors.append(exc)
        return

    if output.exists():
        return
    if result is False:
        errors.append(RuntimeError("HAction FileSaveAs_S returned False."))
    else:
        errors.append(RuntimeError("HAction FileSaveAs_S returned without creating output."))


def _try_hwp_call(method: Any, attempts: list[tuple[Any, ...]], failure_message: str) -> None:
    errors: list[Exception] = []
    for args in attempts:
        try:
            result = method(*args)
        except Exception as exc:
            errors.append(exc)
            continue
        if result is not False:
            return
        errors.append(RuntimeError(failure_message))
    if errors:
        raise RuntimeError(f"{failure_message} {errors[0]}")
    raise RuntimeError(failure_message)


def _quit_application(app: Any) -> None:
    try:
        app.Quit()
    except Exception:
        pass


def _copy_hwp_fallback(
    source: Path,
    output: Path,
    original_size: int | None,
    message: str,
) -> CompressionResult:
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)
    return CompressionResult(
        status=JobStatus.SKIPPED,
        source=source,
        output=output,
        original_size=original_size,
        compressed_size=None,
        message=message,
    )


def _remove_file_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
