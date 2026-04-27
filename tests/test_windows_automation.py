from pathlib import Path

from file_compressor.compressors.windows_automation import (
    compress_hwp,
    compress_legacy_office,
    is_progid_registered,
)
from file_compressor.models import CompressionOptions, CompressionResult, JobStatus


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_hwp_is_skipped_when_hancom_is_unavailable():
    workdir = case_dir("hwp-missing")
    source = workdir / "doc.hwp"
    source.write_bytes(b"hwp")
    output = workdir / "doc_compressed.hwp"

    result = compress_hwp(source, output, automation_available=lambda: False)

    assert result.status is JobStatus.SKIPPED
    assert "Hancom Office" in result.message


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
