from pathlib import Path
import shutil
import tomllib

from file_compressor.compressors.windows_automation import (
    compress_hwp,
    compress_legacy_office,
    default_hancom_available,
    is_progid_registered,
    is_pywin32_available,
)
from file_compressor.models import CompressionOptions, CompressionResult, JobStatus


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_project_declares_pywin32_as_windows_runtime_dependency():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert 'pywin32>=306; platform_system == "Windows"' in data["project"]["dependencies"]


def test_hwp_is_skipped_when_hancom_is_unavailable():
    workdir = case_dir("hwp-missing")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "doc_compressed.hwp"

    result = compress_hwp(source, output, automation_available=lambda: False)

    assert result.status is JobStatus.SKIPPED
    assert "Hancom Office" in result.message


def test_hancom_availability_requires_pywin32_and_registered_progid():
    assert (
        default_hancom_available(
            progid_registered=lambda: True,
            pywin32_available=lambda: False,
        )
        is False
    )
    assert (
        default_hancom_available(
            progid_registered=lambda: False,
            pywin32_available=lambda: True,
        )
        is False
    )
    assert (
        default_hancom_available(
            progid_registered=lambda: True,
            pywin32_available=lambda: True,
        )
        is True
    )


def test_pywin32_availability_checks_win32com_client_import():
    def missing_import(name):
        raise ImportError(name)

    def available_import(name):
        assert name == "win32com.client"
        return object()

    assert is_pywin32_available(import_module=missing_import) is False
    assert is_pywin32_available(import_module=available_import) is True


def test_hwp_opens_and_saves_to_planned_output():
    workdir = case_dir("hwp-save")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "out" / "doc.hwp"
    events = []

    class FakeHwp:
        def RegisterModule(self, dll_name, module_name):
            events.append(("register", dll_name, module_name))

        def Open(self, target):
            events.append(("open", Path(target)))
            return True

        def SaveAs(self, target, format_name):
            events.append(("save_as", Path(target), format_name))
            Path(target).write_bytes(b"saved-hwp")
            return True

        def Quit(self):
            events.append(("quit",))

    def fake_dispatch(progid):
        events.append(("dispatch", progid))
        return FakeHwp()

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=fake_dispatch,
    )

    assert result.status is JobStatus.COMPLETED
    assert result.source == source
    assert result.output == output
    assert result.original_size == len(b"hwp")
    assert result.compressed_size == len(b"saved-hwp")
    assert output.read_bytes() == b"saved-hwp"
    assert events[0] == ("dispatch", "HWPFrame.HwpObject")
    assert any(event[0] == "register" for event in events)
    assert any(event[0] == "open" for event in events)
    assert any(event[0] == "save_as" and event[2] == "HWP" for event in events)
    assert ("quit",) in events


def test_hwp_registers_alternate_file_path_checker_module_name():
    workdir = case_dir("hwp-register-alternate-module")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "out" / "doc.hwp"
    events = []

    class FakeHwp:
        def RegisterModule(self, dll_name, module_name):
            events.append(("register", dll_name, module_name))
            return module_name == "FilePathCheckerModuleExample"

        def Open(self, *args):
            events.append(("open", args))
            return True

        def SaveAs(self, *args):
            Path(args[0]).write_bytes(b"saved-hwp")
            return True

        def Quit(self):
            events.append(("quit",))

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.COMPLETED
    assert ("register", "FilePathCheckDLL", "FilePathCheckerModule") in events
    assert ("register", "FilePathCheckDLL", "FilePathCheckerModuleExample") in events
    assert any(event[0] == "open" for event in events)


def test_hwp_manual_security_prompt_can_complete_when_module_is_unavailable():
    workdir = case_dir("hwp-manual-security-approval")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp-original")
    output = workdir / "out" / "doc.hwp"
    events = []

    class FakeWindow:
        Visible = False

    class FakeWindows:
        def __init__(self, window):
            self.window = window

        def Item(self, index):
            events.append(("window", index))
            return self.window

    class FakeHwp:
        def __init__(self):
            self.window = FakeWindow()
            self.XHwpWindows = FakeWindows(self.window)

        def RegisterModule(self, dll_name, module_name):
            events.append(("register", dll_name, module_name))
            return False

        def Open(self, *args):
            events.append(("open", args, self.window.Visible))
            if not self.window.Visible:
                raise RuntimeError("security prompt was not visible")
            return True

        def SaveAs(self, *args):
            events.append(("save_as", args))
            Path(args[0]).write_bytes(b"saved-after-manual-approval")
            return True

        def Quit(self):
            events.append(("quit",))

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.COMPLETED
    assert result.original_size == len(b"hwp-original")
    assert result.compressed_size == len(b"saved-after-manual-approval")
    assert result.output == output
    assert output.read_bytes() == b"saved-after-manual-approval"
    assert "manual" in result.message
    assert ("window", 0) in events
    assert any(event[0] == "open" and event[2] is True for event in events)
    assert ("quit",) in events


def test_hwp_copies_original_when_manual_security_approval_fails():
    workdir = case_dir("hwp-manual-security-approval-fails")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp-original")
    output = workdir / "out" / "doc.hwp"
    events = []

    class FakeHwp:
        def RegisterModule(self, dll_name, module_name):
            events.append(("register", dll_name, module_name))
            return False

        def Open(self, *args):
            events.append(("open", args))
            return False

        def Quit(self):
            events.append(("quit",))

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.SKIPPED
    assert result.original_size == len(b"hwp-original")
    assert result.compressed_size is None
    assert result.output == output
    assert output.read_bytes() == b"hwp-original"
    assert "manual security approval" in result.message
    assert any(event[0] == "open" for event in events)
    assert ("quit",) in events


def test_hwp_open_and_save_retry_with_format_arguments():
    workdir = case_dir("hwp-open-save-retry")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "out" / "doc.hwp"
    events = []

    class FakeHwp:
        def RegisterModule(self, dll_name, module_name):
            events.append(("register", dll_name, module_name))

        def Open(self, *args):
            events.append(("open", args))
            if len(args) == 1:
                raise TypeError("single argument open rejected")
            return True

        def SaveAs(self, *args):
            events.append(("save_as", args))
            if len(args) == 2:
                raise TypeError("two argument save rejected")
            Path(args[0]).write_bytes(b"saved-hwp")
            return True

        def Quit(self):
            events.append(("quit",))

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.COMPLETED
    assert output.read_bytes() == b"saved-hwp"
    assert ("open", (str(source.resolve()),)) in events
    assert ("open", (str(source.resolve()), "HWP", "")) in events
    assert ("save_as", (str(output.resolve()), "HWP")) in events
    assert ("save_as", (str(output.resolve()), "HWP", "")) in events
    assert ("quit",) in events


def test_hwp_open_retries_with_forceopen_argument():
    workdir = case_dir("hwp-open-forceopen")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "out" / "doc.hwp"
    events = []

    class FakeHwp:
        def RegisterModule(self, dll_name, module_name):
            events.append(("register", dll_name, module_name))

        def Open(self, *args):
            events.append(("open", args))
            if len(args) == 3 and "forceopen:true" in args[2]:
                return True
            return False

        def SaveAs(self, *args):
            events.append(("save_as", args))
            Path(args[0]).write_bytes(b"saved-hwp")
            return True

        def Quit(self):
            events.append(("quit",))

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.COMPLETED
    assert ("open", (str(source.resolve()), "HWP", "forceopen:true")) in events
    assert output.read_bytes() == b"saved-hwp"


def test_hwp_save_as_false_is_success_when_output_was_created():
    workdir = case_dir("hwp-save-false-created-output")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "out" / "doc.hwp"

    class FakeHwp:
        def RegisterModule(self, dll_name, module_name):
            pass

        def Open(self, *args):
            return True

        def SaveAs(self, *args):
            Path(args[0]).write_bytes(b"saved-hwp")
            return False

        def Quit(self):
            pass

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.COMPLETED
    assert output.read_bytes() == b"saved-hwp"


def test_hwp_save_uses_hwp_action_fallback_when_save_as_does_not_create_output():
    workdir = case_dir("hwp-action-save-fallback")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "out" / "doc.hwp"
    events = []

    class FakeFileOpenSave:
        def __init__(self):
            self.HSet = object()
            self.filename = ""
            self.Format = ""

    class FakeHAction:
        def __init__(self, params):
            self.params = params

        def GetDefault(self, action_name, hset):
            events.append(("get_default", action_name, hset))
            return True

        def Execute(self, action_name, hset):
            events.append(("execute", action_name, hset, self.params.filename, self.params.Format))
            Path(self.params.filename).write_bytes(b"saved-by-action")
            return True

    class FakeHwp:
        def __init__(self):
            self.HParameterSet = type("FakeParameterSet", (), {})()
            self.HParameterSet.HFileOpenSave = FakeFileOpenSave()
            self.HAction = FakeHAction(self.HParameterSet.HFileOpenSave)

        def RegisterModule(self, dll_name, module_name):
            pass

        def Open(self, *args):
            return True

        def SaveAs(self, *args):
            events.append(("save_as", args))
            return False

        def Quit(self):
            pass

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.COMPLETED
    assert output.read_bytes() == b"saved-by-action"
    assert any(event[0] == "get_default" and event[1] == "FileSaveAs_S" for event in events)
    assert any(event[0] == "execute" and event[3] == str(output.resolve()) for event in events)


def test_hwp_quit_failure_does_not_mask_successful_save():
    workdir = case_dir("hwp-quit-fails-after-save")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "out" / "doc.hwp"

    class FakeHwp:
        def RegisterModule(self, dll_name, module_name):
            pass

        def Open(self, *args):
            return True

        def SaveAs(self, *args):
            Path(args[0]).write_bytes(b"saved-hwp")
            return True

        def Quit(self):
            raise RuntimeError("quit failed")

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.COMPLETED
    assert output.read_bytes() == b"saved-hwp"


def test_hwp_returns_failed_and_quits_when_save_fails():
    workdir = case_dir("hwp-save-fails")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "doc_compressed.hwp"
    events = []

    class FakeHwp:
        def RegisterModule(self, dll_name, module_name):
            events.append(("register", dll_name, module_name))

        def Open(self, target):
            events.append(("open", Path(target)))
            return True

        def SaveAs(self, target, format_name):
            events.append(("save_as", Path(target), format_name))
            raise RuntimeError("save failed")

        def Quit(self):
            events.append(("quit",))

    result = compress_hwp(
        source,
        output,
        automation_available=lambda: True,
        dispatch=lambda progid: FakeHwp(),
    )

    assert result.status is JobStatus.FAILED
    assert result.source == source
    assert "save failed" in result.message
    assert ("quit",) in events


def test_legacy_office_is_skipped_when_office_is_unavailable():
    workdir = case_dir("legacy-office-missing")
    source = workdir / "legacy.xls"
    source.write_bytes(b"xls")
    output = workdir / "legacy_compressed.xls"

    result = compress_legacy_office(source, output, automation_available=lambda: False)

    assert result.status is JobStatus.SKIPPED
    assert "Microsoft Office" in result.message


def test_legacy_excel_converts_to_xlsx_then_compresses(monkeypatch):
    workdir = case_dir("legacy-excel-convert")
    source = workdir / "legacy.xls"
    source.write_bytes(b"xls")
    output = workdir / "legacy_compressed.xlsx"
    options = CompressionOptions(jpeg_quality=65)
    events = []

    class FakeWorkbook:
        def SaveAs(self, target, FileFormat):
            events.append(("save_as", Path(target), FileFormat))
            Path(target).write_bytes(b"xlsx")

        def Close(self, SaveChanges=False):
            events.append(("close", SaveChanges))

    class FakeExcel:
        def __init__(self):
            self.Workbooks = self
            self.DisplayAlerts = True

        def Open(self, target):
            events.append(("open", Path(target)))
            return FakeWorkbook()

        def Quit(self):
            events.append(("quit",))

    def fake_dispatch(progid):
        events.append(("dispatch", progid))
        return FakeExcel()

    def fake_compress_zip_document(converted, selected_output, *, options=None):
        events.append(("compress", converted, selected_output, options))
        return CompressionResult(
            status=JobStatus.COMPLETED,
            source=converted,
            output=selected_output,
            original_size=20,
            compressed_size=10,
            message="Compressed",
        )

    monkeypatch.setattr(
        "file_compressor.compressors.windows_automation.compress_zip_document",
        fake_compress_zip_document,
    )

    result = compress_legacy_office(
        source,
        output,
        options=options,
        automation_available=lambda: True,
        dispatch=fake_dispatch,
    )

    assert result.status is JobStatus.COMPLETED
    assert result.source == source
    assert result.output == output
    assert result.original_size == len(b"xls")
    assert events[0] == ("dispatch", "Excel.Application")
    assert ("save_as", events[2][1], 51) in events
    compress_event = [event for event in events if event[0] == "compress"][0]
    assert compress_event[1].suffix == ".xlsx"
    assert compress_event[1] != output
    assert compress_event[2] == output
    assert compress_event[3] is options
    assert ("close", False) in events
    assert ("quit",) in events


def test_legacy_powerpoint_converts_to_pptx_then_compresses(monkeypatch):
    workdir = case_dir("legacy-powerpoint-convert")
    source = workdir / "slides.ppt"
    source.write_bytes(b"ppt")
    output = workdir / "slides_compressed.pptx"
    events = []

    class FakePresentation:
        def SaveAs(self, target, FileFormat):
            events.append(("save_as", Path(target), FileFormat))
            Path(target).write_bytes(b"pptx")

        def Close(self):
            events.append(("close",))

    class FakePowerPoint:
        def __init__(self):
            self.Presentations = self

        def Open(self, target, WithWindow=False):
            events.append(("open", Path(target), WithWindow))
            return FakePresentation()

        def Quit(self):
            events.append(("quit",))

    def fake_dispatch(progid):
        events.append(("dispatch", progid))
        return FakePowerPoint()

    def fake_compress_zip_document(converted, selected_output, *, options=None):
        events.append(("compress", converted, selected_output))
        return CompressionResult(
            status=JobStatus.COMPLETED,
            source=converted,
            output=selected_output,
            compressed_size=12,
            message="Compressed",
        )

    monkeypatch.setattr(
        "file_compressor.compressors.windows_automation.compress_zip_document",
        fake_compress_zip_document,
    )

    result = compress_legacy_office(
        source,
        output,
        automation_available=lambda: True,
        dispatch=fake_dispatch,
    )

    assert result.status is JobStatus.COMPLETED
    assert result.source == source
    assert result.output == output
    assert events[0] == ("dispatch", "PowerPoint.Application")
    assert any(event[0] == "open" and event[2] is False for event in events)
    assert any(event[0] == "save_as" and event[2] == 24 for event in events)
    assert any(event[0] == "compress" and event[1].suffix == ".pptx" for event in events)
    assert ("close",) in events
    assert ("quit",) in events


def test_is_progid_registered_uses_registry_without_launching_application():
    opened = []

    class FakeKey:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    def fake_open_key(root, path):
        opened.append((root, path))
        return FakeKey()

    assert is_progid_registered("Excel.Application", open_key=fake_open_key) is True
    assert opened[0][1] == "Excel.Application\\CLSID"


def test_is_progid_registered_returns_false_when_key_is_missing():
    def fake_open_key(root, path):
        raise FileNotFoundError(path)

    assert is_progid_registered("Excel.Application", open_key=fake_open_key) is False
