from pathlib import Path
import shutil
import sys

from file_compressor.dependencies import DependencyStatus, detect_ghostscript, detect_jpegtran, detect_tesseract


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def test_detect_ghostscript_reports_missing_when_lookup_fails():
    status = detect_ghostscript(which=lambda _: None)

    assert status == DependencyStatus(available=False, executable=None)


def test_detect_ghostscript_reports_available_path():
    status = detect_ghostscript(which=lambda _: "C:/Tools/gswin64c.exe")

    assert status == DependencyStatus(available=True, executable="C:/Tools/gswin64c.exe")


def test_detect_tesseract_prefers_bundled_executable():
    app_dir = case_dir("dependency-bundled-tesseract")
    bundled = app_dir / "tools" / "tesseract" / "tesseract.exe"
    bundled.parent.mkdir(parents=True)
    bundled.write_bytes(b"exe")

    status = detect_tesseract(
        which=lambda _: "C:/System/tesseract.exe",
        app_dir=app_dir,
    )

    assert status == DependencyStatus(available=True, executable=str(bundled))


def test_detect_tesseract_falls_back_to_path_lookup():
    app_dir = case_dir("dependency-system-tesseract")

    status = detect_tesseract(
        which=lambda name: "C:/System/tesseract.exe" if name == "tesseract" else None,
        app_dir=app_dir,
    )

    assert status == DependencyStatus(available=True, executable="C:/System/tesseract.exe")


def test_detect_jpegtran_prefers_bundled_executable():
    app_dir = case_dir("dependency-bundled-jpegtran")
    bundled = app_dir / "tools" / "jpegtran" / "jpegtran.exe"
    bundled.parent.mkdir(parents=True)
    bundled.write_bytes(b"exe")

    status = detect_jpegtran(
        which=lambda _: "C:/System/jpegtran.exe",
        app_dir=app_dir,
    )

    assert status == DependencyStatus(available=True, executable=str(bundled))


def test_detect_jpegtran_prefers_pyinstaller_runtime_executable(monkeypatch):
    app_dir = case_dir("dependency-pyinstaller-jpegtran-app")
    runtime_dir = case_dir("dependency-pyinstaller-jpegtran-runtime")
    app_bundled = app_dir / "tools" / "jpegtran" / "jpegtran.exe"
    runtime_bundled = runtime_dir / "tools" / "jpegtran" / "jpegtran.exe"
    app_bundled.parent.mkdir(parents=True)
    runtime_bundled.parent.mkdir(parents=True)
    app_bundled.write_bytes(b"app")
    runtime_bundled.write_bytes(b"runtime")
    monkeypatch.setattr(sys, "_MEIPASS", str(runtime_dir), raising=False)

    status = detect_jpegtran(
        which=lambda _: "C:/System/jpegtran.exe",
        app_dir=app_dir,
    )

    assert status == DependencyStatus(available=True, executable=str(runtime_bundled))


def test_detect_jpegtran_falls_back_to_path_lookup():
    app_dir = case_dir("dependency-system-jpegtran")

    status = detect_jpegtran(
        which=lambda name: "C:/System/jpegtran.exe" if name == "jpegtran" else None,
        app_dir=app_dir,
    )

    assert status == DependencyStatus(available=True, executable="C:/System/jpegtran.exe")
