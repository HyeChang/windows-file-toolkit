from dataclasses import dataclass
from pathlib import Path
from shutil import which as default_which
import sys
from typing import Callable


GHOSTSCRIPT_DOWNLOAD_URL = "https://ghostscript.com/releases/gsdnld.html"
TESSERACT_DOWNLOAD_URL = "https://github.com/UB-Mannheim/tesseract/wiki"


@dataclass(frozen=True)
class DependencyStatus:
    available: bool
    executable: str | None = None


def detect_ghostscript(which: Callable[[str], str | None] = default_which) -> DependencyStatus:
    executable = which("gswin64c") or which("gswin32c") or which("gs")
    return DependencyStatus(available=executable is not None, executable=executable)


def detect_tesseract(
    which: Callable[[str], str | None] = default_which,
    *,
    app_dir: Path | None = None,
) -> DependencyStatus:
    bundled = _bundled_tesseract_path(app_dir)
    executable = str(bundled) if bundled.exists() else which("tesseract")
    return DependencyStatus(available=executable is not None, executable=executable)


def detect_jpegtran(
    which: Callable[[str], str | None] = default_which,
    *,
    app_dir: Path | None = None,
) -> DependencyStatus:
    bundled = _first_existing_path(_bundled_jpegtran_paths(app_dir))
    executable = str(bundled) if bundled is not None else which("jpegtran")
    return DependencyStatus(available=executable is not None, executable=executable)


def _bundled_tesseract_path(app_dir: Path | None = None) -> Path:
    root = app_dir or _app_dir()
    return root / "tools" / "tesseract" / "tesseract.exe"


def _bundled_jpegtran_path(app_dir: Path | None = None) -> Path:
    root = app_dir or _app_dir()
    return root / "tools" / "jpegtran" / "jpegtran.exe"


def _bundled_jpegtran_paths(app_dir: Path | None = None) -> list[Path]:
    paths: list[Path] = []
    runtime_dir = _pyinstaller_runtime_dir()
    if runtime_dir is not None:
        paths.append(runtime_dir / "tools" / "jpegtran" / "jpegtran.exe")
    paths.append(_bundled_jpegtran_path(app_dir))
    return paths


def _first_existing_path(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _pyinstaller_runtime_dir() -> Path | None:
    runtime_dir = getattr(sys, "_MEIPASS", None)
    return Path(runtime_dir) if runtime_dir else None


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()
