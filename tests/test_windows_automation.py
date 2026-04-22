from pathlib import Path

from file_compressor.compressors.windows_automation import (
    compress_hwp,
    compress_legacy_office,
    is_progid_registered,
)
from file_compressor.models import JobStatus


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
