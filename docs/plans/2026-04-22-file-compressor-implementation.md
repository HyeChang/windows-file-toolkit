# File Compressor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Windows desktop app that compresses Excel, PowerPoint, PDF, and Korean document files while preserving originals.

**Architecture:** Use a PySide6 desktop shell over a testable Python compression engine. The engine classifies files, creates safe output paths, dispatches to format-specific compressors, and returns per-file job results without letting one failure stop the batch.

**Tech Stack:** Python 3.11+, PySide6, Pillow, pytest, PyInstaller, optional Ghostscript, optional Hancom Office, optional Microsoft Office automation.

---

## Task 1: Create Python Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/file_compressor/__init__.py`
- Create: `src/file_compressor_app/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create package metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "file-compressor"
version = "0.1.0"
description = "Windows desktop app for compressing office documents and PDFs"
requires-python = ">=3.11"
dependencies = [
  "Pillow>=10.0",
  "PySide6>=6.7",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pyinstaller>=6.0",
]
windows = [
  "pywin32>=306",
]

[project.scripts]
file-compressor = "file_compressor_app.main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 2: Add a short README**

Create `README.md` with:

```markdown
# File Compressor

Windows desktop app for reducing the size of Excel, PowerPoint, PDF, HWPX, and conditionally supported HWP files.

The app preserves original files and writes compressed copies next to the source file.
```

**Step 3: Add empty packages**

Create empty `__init__.py` files in `src/file_compressor`, `src/file_compressor_app`, and `tests`.

**Step 4: Run import check**

Run: `python -m pytest -q`

Expected: pytest starts successfully and reports no tests collected.

**Step 5: Commit**

```bash
git add pyproject.toml README.md src tests
git commit -m "chore: scaffold python project"
```

---

## Task 2: Add Safe Output Path Generation

**Files:**
- Create: `tests/test_paths.py`
- Create: `src/file_compressor/paths.py`

**Step 1: Write the failing tests**

Create `tests/test_paths.py`:

```python
from pathlib import Path

from file_compressor.paths import compressed_output_path


def test_compressed_output_path_adds_suffix_next_to_source(tmp_path: Path):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"source")

    result = compressed_output_path(source)

    assert result == tmp_path / "report_compressed.pdf"


def test_compressed_output_path_uses_number_when_target_exists(tmp_path: Path):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"source")
    (tmp_path / "report_compressed.pdf").write_bytes(b"existing")
    (tmp_path / "report_compressed_2.pdf").write_bytes(b"existing")

    result = compressed_output_path(source)

    assert result == tmp_path / "report_compressed_3.pdf"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_paths.py -q`

Expected: FAIL because `file_compressor.paths` does not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor/paths.py`:

```python
from pathlib import Path


def compressed_output_path(source: Path) -> Path:
    base = source.with_name(f"{source.stem}_compressed{source.suffix}")
    if not base.exists():
        return base

    counter = 2
    while True:
        candidate = source.with_name(f"{source.stem}_compressed_{counter}{source.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_paths.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_paths.py src/file_compressor/paths.py
git commit -m "feat: generate safe compressed output paths"
```

---

## Task 3: Add File Classification and Result Models

**Files:**
- Create: `tests/test_formats.py`
- Create: `src/file_compressor/models.py`
- Create: `src/file_compressor/formats.py`

**Step 1: Write the failing tests**

Create `tests/test_formats.py`:

```python
from pathlib import Path

from file_compressor.formats import classify_file
from file_compressor.models import FileKind, JobStatus


def test_classifies_zip_based_office_files_case_insensitively():
    assert classify_file(Path("book.XLSX")) is FileKind.OOXML
    assert classify_file(Path("deck.pptm")) is FileKind.OOXML


def test_classifies_korean_and_pdf_files():
    assert classify_file(Path("doc.hwpx")) is FileKind.HWPX
    assert classify_file(Path("doc.hwp")) is FileKind.HWP
    assert classify_file(Path("doc.pdf")) is FileKind.PDF


def test_classifies_legacy_office_and_unsupported_files():
    assert classify_file(Path("legacy.xls")) is FileKind.LEGACY_OFFICE
    assert classify_file(Path("notes.txt")) is FileKind.UNSUPPORTED


def test_job_status_values_are_stable_for_ui():
    assert [status.value for status in JobStatus] == [
        "pending",
        "processing",
        "completed",
        "skipped",
        "failed",
    ]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_formats.py -q`

Expected: FAIL because models and format classification do not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor/models.py`:

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FileKind(Enum):
    OOXML = "ooxml"
    HWPX = "hwpx"
    PDF = "pdf"
    HWP = "hwp"
    LEGACY_OFFICE = "legacy_office"
    UNSUPPORTED = "unsupported"


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class CompressionResult:
    status: JobStatus
    source: Path
    output: Path | None = None
    original_size: int | None = None
    compressed_size: int | None = None
    message: str = ""
```

Create `src/file_compressor/formats.py`:

```python
from pathlib import Path

from file_compressor.models import FileKind


OOXML_EXTENSIONS = {".xlsx", ".xlsm", ".pptx", ".pptm"}
LEGACY_OFFICE_EXTENSIONS = {".xls", ".ppt"}


def classify_file(path: Path) -> FileKind:
    suffix = path.suffix.lower()
    if suffix in OOXML_EXTENSIONS:
        return FileKind.OOXML
    if suffix == ".hwpx":
        return FileKind.HWPX
    if suffix == ".pdf":
        return FileKind.PDF
    if suffix == ".hwp":
        return FileKind.HWP
    if suffix in LEGACY_OFFICE_EXTENSIONS:
        return FileKind.LEGACY_OFFICE
    return FileKind.UNSUPPORTED
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_formats.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_formats.py src/file_compressor/models.py src/file_compressor/formats.py
git commit -m "feat: classify supported document formats"
```

---

## Task 4: Add Dependency Detection

**Files:**
- Create: `tests/test_dependencies.py`
- Create: `src/file_compressor/dependencies.py`

**Step 1: Write the failing tests**

Create `tests/test_dependencies.py`:

```python
from file_compressor.dependencies import DependencyStatus, detect_ghostscript


def test_detect_ghostscript_reports_missing_when_lookup_fails():
    status = detect_ghostscript(which=lambda _: None)

    assert status == DependencyStatus(available=False, executable=None)


def test_detect_ghostscript_reports_available_path():
    status = detect_ghostscript(which=lambda _: "C:/Tools/gswin64c.exe")

    assert status == DependencyStatus(available=True, executable="C:/Tools/gswin64c.exe")
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dependencies.py -q`

Expected: FAIL because dependency detection does not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor/dependencies.py`:

```python
from dataclasses import dataclass
from shutil import which as default_which
from typing import Callable


@dataclass(frozen=True)
class DependencyStatus:
    available: bool
    executable: str | None = None


def detect_ghostscript(which: Callable[[str], str | None] = default_which) -> DependencyStatus:
    executable = which("gswin64c") or which("gswin32c") or which("gs")
    return DependencyStatus(available=executable is not None, executable=executable)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dependencies.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_dependencies.py src/file_compressor/dependencies.py
git commit -m "feat: detect external compression dependencies"
```

---

## Task 5: Add Image Optimization

**Files:**
- Create: `tests/test_images.py`
- Create: `src/file_compressor/images.py`

**Step 1: Write the failing tests**

Create `tests/test_images.py`:

```python
from io import BytesIO

from PIL import Image

from file_compressor.images import optimize_image_bytes


def make_image(format_name: str, size=(2000, 1200)) -> bytes:
    image = Image.new("RGB", size, color=(220, 20, 60))
    buffer = BytesIO()
    image.save(buffer, format=format_name)
    return buffer.getvalue()


def test_optimize_jpeg_reduces_large_image_dimensions():
    original = make_image("JPEG")

    optimized = optimize_image_bytes("image/jpeg", original, max_dimension=800, jpeg_quality=75)

    result = Image.open(BytesIO(optimized))
    assert max(result.size) <= 800
    assert len(optimized) < len(original)


def test_optimize_returns_original_when_format_is_unknown():
    original = b"not an image"

    optimized = optimize_image_bytes("application/octet-stream", original)

    assert optimized == original
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_images.py -q`

Expected: FAIL because image optimizer does not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor/images.py`:

```python
from io import BytesIO

from PIL import Image, ImageOps


SUPPORTED_CONTENT_TYPES = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
}


def optimize_image_bytes(
    content_type: str,
    data: bytes,
    *,
    max_dimension: int = 1600,
    jpeg_quality: int = 78,
) -> bytes:
    image_format = SUPPORTED_CONTENT_TYPES.get(content_type.lower())
    if image_format is None:
        return data

    try:
        with Image.open(BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail((max_dimension, max_dimension))

            output = BytesIO()
            if image_format == "JPEG":
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
                image.save(output, format="JPEG", quality=jpeg_quality, optimize=True)
            else:
                image.save(output, format="PNG", optimize=True)

            optimized = output.getvalue()
            return optimized if len(optimized) < len(data) else data
    except Exception:
        return data
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_images.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_images.py src/file_compressor/images.py
git commit -m "feat: optimize embedded document images"
```

---

## Task 6: Add ZIP Package Rewriter

**Files:**
- Create: `tests/test_zip_packages.py`
- Create: `src/file_compressor/zip_packages.py`

**Step 1: Write the failing tests**

Create `tests/test_zip_packages.py`:

```python
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from file_compressor.zip_packages import rewrite_zip_package


def test_rewrite_zip_package_preserves_non_media_entries(tmp_path: Path):
    source = tmp_path / "source.zip"
    output = tmp_path / "output.zip"
    with ZipFile(source, "w", ZIP_DEFLATED) as archive:
        archive.writestr("doc.xml", "<doc />")
        archive.writestr("media/image.jpg", b"image-data")

    rewrite_zip_package(
        source,
        output,
        transform=lambda name, data: b"smaller" if name.endswith(".jpg") else data,
    )

    with ZipFile(output) as archive:
        assert archive.read("doc.xml") == b"<doc />"
        assert archive.read("media/image.jpg") == b"smaller"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_zip_packages.py -q`

Expected: FAIL because ZIP rewriter does not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor/zip_packages.py`:

```python
from collections.abc import Callable
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


Transform = Callable[[str, bytes], bytes]


def rewrite_zip_package(source: Path, output: Path, transform: Transform) -> None:
    with ZipFile(source, "r") as input_archive, ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as output_archive:
        for info in input_archive.infolist():
            data = input_archive.read(info.filename)
            transformed = transform(info.filename, data)
            new_info = ZipInfo(filename=info.filename, date_time=info.date_time)
            new_info.external_attr = info.external_attr
            new_info.comment = info.comment
            new_info.extra = info.extra
            output_archive.writestr(new_info, transformed, compress_type=ZIP_DEFLATED)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_zip_packages.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_zip_packages.py src/file_compressor/zip_packages.py
git commit -m "feat: rewrite compressed document packages"
```

---

## Task 7: Add OOXML and HWPX Package Compressors

**Files:**
- Create: `tests/test_package_compressors.py`
- Create: `src/file_compressor/compressors/__init__.py`
- Create: `src/file_compressor/compressors/package.py`

**Step 1: Write the failing tests**

Create `tests/test_package_compressors.py`:

```python
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

from file_compressor.compressors.package import compress_zip_document
from file_compressor.models import JobStatus


def make_jpeg() -> bytes:
    image = Image.new("RGB", (2000, 1200), color=(0, 80, 180))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_compress_zip_document_writes_output_and_preserves_entries(tmp_path: Path):
    source = tmp_path / "deck.pptx"
    output = tmp_path / "deck_compressed.pptx"
    with ZipFile(source, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("ppt/media/image1.jpeg", make_jpeg())

    result = compress_zip_document(source, output)

    assert result.status is JobStatus.COMPLETED
    assert result.output == output
    assert output.exists()
    with ZipFile(output) as archive:
        assert archive.read("[Content_Types].xml") == b"<Types />"
        assert len(archive.read("ppt/media/image1.jpeg")) < len(make_jpeg())
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_package_compressors.py -q`

Expected: FAIL because package compressor does not exist.

**Step 3: Implement minimal code**

Create empty `src/file_compressor/compressors/__init__.py`.

Create `src/file_compressor/compressors/package.py`:

```python
from pathlib import Path

from file_compressor.images import optimize_image_bytes
from file_compressor.models import CompressionResult, JobStatus
from file_compressor.zip_packages import rewrite_zip_package


CONTENT_TYPES_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def compress_zip_document(source: Path, output: Path) -> CompressionResult:
    original_size = source.stat().st_size

    def transform(name: str, data: bytes) -> bytes:
        suffix = Path(name).suffix.lower()
        content_type = CONTENT_TYPES_BY_EXTENSION.get(suffix)
        if content_type is None:
            return data
        return optimize_image_bytes(content_type, data)

    rewrite_zip_package(source, output, transform)
    return CompressionResult(
        status=JobStatus.COMPLETED,
        source=source,
        output=output,
        original_size=original_size,
        compressed_size=output.stat().st_size,
        message="Compressed",
    )
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_package_compressors.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_package_compressors.py src/file_compressor/compressors
git commit -m "feat: compress zip-based document formats"
```

---

## Task 8: Add PDF Compressor

**Files:**
- Create: `tests/test_pdf_compressor.py`
- Create: `src/file_compressor/compressors/pdf.py`

**Step 1: Write the failing tests**

Create `tests/test_pdf_compressor.py`:

```python
from pathlib import Path

from file_compressor.compressors.pdf import build_ghostscript_command, compress_pdf
from file_compressor.dependencies import DependencyStatus
from file_compressor.models import JobStatus


def test_build_ghostscript_command_uses_screen_setting(tmp_path: Path):
    source = tmp_path / "input.pdf"
    output = tmp_path / "output.pdf"

    command = build_ghostscript_command("gs", source, output)

    assert command[0] == "gs"
    assert "-sDEVICE=pdfwrite" in command
    assert "-dPDFSETTINGS=/screen" in command
    assert f"-sOutputFile={output}" in command
    assert str(source) == command[-1]


def test_compress_pdf_skips_when_ghostscript_missing(tmp_path: Path):
    source = tmp_path / "input.pdf"
    source.write_bytes(b"%PDF-1.4")
    output = tmp_path / "output.pdf"

    result = compress_pdf(source, output, dependency=DependencyStatus(False))

    assert result.status is JobStatus.SKIPPED
    assert result.output is None
    assert "Ghostscript" in result.message
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pdf_compressor.py -q`

Expected: FAIL because PDF compressor does not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor/compressors/pdf.py`:

```python
from pathlib import Path
import subprocess

from file_compressor.dependencies import DependencyStatus, detect_ghostscript
from file_compressor.models import CompressionResult, JobStatus


def build_ghostscript_command(executable: str, source: Path, output: Path) -> list[str]:
    return [
        executable,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/screen",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output}",
        str(source),
    ]


def compress_pdf(
    source: Path,
    output: Path,
    *,
    dependency: DependencyStatus | None = None,
) -> CompressionResult:
    dependency = dependency or detect_ghostscript()
    original_size = source.stat().st_size
    if not dependency.available or dependency.executable is None:
        return CompressionResult(
            status=JobStatus.SKIPPED,
            source=source,
            original_size=original_size,
            message="Ghostscript is required for PDF compression.",
        )

    command = build_ghostscript_command(dependency.executable, source, output)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0 or not output.exists():
        return CompressionResult(
            status=JobStatus.FAILED,
            source=source,
            original_size=original_size,
            message=completed.stderr.strip() or "Ghostscript failed.",
        )

    return CompressionResult(
        status=JobStatus.COMPLETED,
        source=source,
        output=output,
        original_size=original_size,
        compressed_size=output.stat().st_size,
        message="Compressed",
    )
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pdf_compressor.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_pdf_compressor.py src/file_compressor/compressors/pdf.py
git commit -m "feat: add ghostscript pdf compression"
```

---

## Task 9: Add Conditional Windows Automation Adapters

**Files:**
- Create: `tests/test_windows_automation.py`
- Create: `src/file_compressor/compressors/windows_automation.py`

**Step 1: Write the failing tests**

Create `tests/test_windows_automation.py`:

```python
from pathlib import Path

from file_compressor.compressors.windows_automation import compress_hwp, compress_legacy_office
from file_compressor.models import JobStatus


def test_hwp_is_skipped_when_hancom_is_unavailable(tmp_path: Path):
    source = tmp_path / "doc.hwp"
    source.write_bytes(b"hwp")
    output = tmp_path / "doc_compressed.hwp"

    result = compress_hwp(source, output, automation_available=lambda: False)

    assert result.status is JobStatus.SKIPPED
    assert "Hancom Office" in result.message


def test_legacy_office_is_skipped_when_office_is_unavailable(tmp_path: Path):
    source = tmp_path / "legacy.xls"
    source.write_bytes(b"xls")
    output = tmp_path / "legacy_compressed.xls"

    result = compress_legacy_office(source, output, automation_available=lambda: False)

    assert result.status is JobStatus.SKIPPED
    assert "Microsoft Office" in result.message
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_windows_automation.py -q`

Expected: FAIL because Windows automation adapter does not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor/compressors/windows_automation.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_windows_automation.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_windows_automation.py src/file_compressor/compressors/windows_automation.py
git commit -m "feat: add conditional windows document adapters"
```

---

## Task 10: Add Batch Compression Engine

**Files:**
- Create: `tests/test_engine.py`
- Create: `src/file_compressor/engine.py`

**Step 1: Write the failing tests**

Create `tests/test_engine.py`:

```python
from pathlib import Path

from file_compressor.engine import compress_file, compress_many
from file_compressor.models import JobStatus


def test_unsupported_file_is_skipped(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_text("hello")

    result = compress_file(source)

    assert result.status is JobStatus.SKIPPED
    assert "Unsupported" in result.message


def test_batch_continues_after_failed_file(tmp_path: Path):
    bad = tmp_path / "missing.xlsx"
    unsupported = tmp_path / "notes.txt"
    unsupported.write_text("hello")

    results = list(compress_many([bad, unsupported]))

    assert [result.status for result in results] == [JobStatus.FAILED, JobStatus.SKIPPED]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_engine.py -q`

Expected: FAIL because the engine does not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor/engine.py`:

```python
from collections.abc import Iterable, Iterator
from pathlib import Path

from file_compressor.compressors.package import compress_zip_document
from file_compressor.compressors.pdf import compress_pdf
from file_compressor.compressors.windows_automation import compress_hwp, compress_legacy_office
from file_compressor.formats import classify_file
from file_compressor.models import CompressionResult, FileKind, JobStatus
from file_compressor.paths import compressed_output_path


def compress_file(source: Path) -> CompressionResult:
    try:
        if not source.exists():
            return CompressionResult(status=JobStatus.FAILED, source=source, message="Source file does not exist.")

        kind = classify_file(source)
        if kind is FileKind.UNSUPPORTED:
            return CompressionResult(
                status=JobStatus.SKIPPED,
                source=source,
                original_size=source.stat().st_size,
                message="Unsupported file type.",
            )

        output = compressed_output_path(source)
        if kind in {FileKind.OOXML, FileKind.HWPX}:
            return compress_zip_document(source, output)
        if kind is FileKind.PDF:
            return compress_pdf(source, output)
        if kind is FileKind.HWP:
            return compress_hwp(source, output)
        if kind is FileKind.LEGACY_OFFICE:
            return compress_legacy_office(source, output)

        return CompressionResult(status=JobStatus.SKIPPED, source=source, message="Unsupported file type.")
    except Exception as exc:
        return CompressionResult(status=JobStatus.FAILED, source=source, message=str(exc))


def compress_many(paths: Iterable[Path]) -> Iterator[CompressionResult]:
    for path in paths:
        yield compress_file(path)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_engine.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_engine.py src/file_compressor/engine.py
git commit -m "feat: add batch compression engine"
```

---

## Task 11: Add UI View Model

**Files:**
- Create: `tests/test_view_model.py`
- Create: `src/file_compressor_app/view_model.py`

**Step 1: Write the failing tests**

Create `tests/test_view_model.py`:

```python
from pathlib import Path

from file_compressor.models import CompressionResult, JobStatus
from file_compressor_app.view_model import FileJob, result_to_job


def test_file_job_displays_size_in_kb():
    job = FileJob(path=Path("report.pdf"), original_size=1536)

    assert job.original_size_text == "1.5 KB"


def test_result_to_job_copies_output_and_status():
    result = CompressionResult(
        status=JobStatus.COMPLETED,
        source=Path("report.pdf"),
        output=Path("report_compressed.pdf"),
        original_size=2000,
        compressed_size=1000,
        message="Compressed",
    )

    job = result_to_job(result)

    assert job.status == "completed"
    assert job.output_path == Path("report_compressed.pdf")
    assert job.compressed_size_text == "1000 B"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_view_model.py -q`

Expected: FAIL because UI view model does not exist.

**Step 3: Implement minimal code**

Create `src/file_compressor_app/view_model.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from file_compressor.models import CompressionResult, JobStatus


def format_size(size: int | None) -> str:
    if size is None:
        return "-"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


@dataclass
class FileJob:
    path: Path
    status: str = JobStatus.PENDING.value
    original_size: int | None = None
    compressed_size: int | None = None
    output_path: Path | None = None
    message: str = ""

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def kind(self) -> str:
        return self.path.suffix.lower().lstrip(".") or "-"

    @property
    def original_size_text(self) -> str:
        return format_size(self.original_size)

    @property
    def compressed_size_text(self) -> str:
        return format_size(self.compressed_size)

    @property
    def output_text(self) -> str:
        return str(self.output_path) if self.output_path else "-"


def result_to_job(result: CompressionResult) -> FileJob:
    return FileJob(
        path=result.source,
        status=result.status.value,
        original_size=result.original_size,
        compressed_size=result.compressed_size,
        output_path=result.output,
        message=result.message,
    )
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_view_model.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_view_model.py src/file_compressor_app/view_model.py
git commit -m "feat: add ui file job view model"
```

---

## Task 12: Add PySide6 Desktop UI

**Files:**
- Create: `src/file_compressor_app/ui.py`
- Create: `src/file_compressor_app/main.py`

**Step 1: Implement thin UI shell**

Create `src/file_compressor_app/ui.py`:

```python
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from file_compressor.engine import compress_file
from file_compressor_app.view_model import FileJob, result_to_job


class DropTable(QTableWidget):
    def __init__(self, on_files):
        super().__init__(0, 6)
        self.on_files = on_files
        self.setAcceptDrops(True)
        self.setHorizontalHeaderLabels(["File", "Type", "Original", "Status", "Compressed", "Output"])
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.on_files(paths)
        event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Compressor")
        self.resize(980, 560)
        self.jobs: list[FileJob] = []

        self.table = DropTable(self.add_files)
        self.status_label = QLabel("Add files to start.")
        self.add_button = QPushButton("Add files")
        self.start_button = QPushButton("Start compression")

        self.add_button.clicked.connect(self.pick_files)
        self.start_button.clicked.connect(self.compress_jobs)

        actions = QHBoxLayout()
        actions.addWidget(self.add_button)
        actions.addWidget(self.start_button)
        actions.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files",
            "",
            "Documents (*.xlsx *.xlsm *.pptx *.pptm *.pdf *.hwpx *.hwp *.xls *.ppt);;All files (*.*)",
        )
        self.add_files([Path(file) for file in files])

    def add_files(self, paths: list[Path]):
        for path in paths:
            if path.is_file():
                size = path.stat().st_size
                self.jobs.append(FileJob(path=path, original_size=size))
        self.refresh_table()
        self.status_label.setText(f"{len(self.jobs)} file(s) ready.")

    def compress_jobs(self):
        for index, job in enumerate(list(self.jobs)):
            self.jobs[index].status = "processing"
            self.refresh_table()
            QApplication.processEvents()

            result = compress_file(job.path)
            self.jobs[index] = result_to_job(result)
            self.refresh_table()
            QApplication.processEvents()
        self.status_label.setText("Compression finished.")

    def refresh_table(self):
        self.table.setRowCount(len(self.jobs))
        for row, job in enumerate(self.jobs):
            values = [
                job.name,
                job.kind,
                job.original_size_text,
                job.status,
                job.compressed_size_text,
                job.output_text,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(job.message if column == 3 else value)
                if column == 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()
```

Create `src/file_compressor_app/main.py`:

```python
import sys

from PySide6.QtWidgets import QApplication

from file_compressor_app.ui import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 2: Run tests**

Run: `python -m pytest -q`

Expected: PASS.

**Step 3: Run smoke check**

Run: `python -m file_compressor_app.main`

Expected: The desktop window opens. Close it manually after verifying the table, add button, and start button render.

**Step 4: Commit**

```bash
git add src/file_compressor_app/ui.py src/file_compressor_app/main.py
git commit -m "feat: add desktop compression ui"
```

---

## Task 13: Add PyInstaller Packaging

**Files:**
- Create: `file-compressor.spec`
- Create: `scripts/build_exe.ps1`

**Step 1: Add PyInstaller spec**

Create `file-compressor.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["src/file_compressor_app/main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FileCompressor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

Create `scripts/build_exe.ps1`:

```powershell
python -m PyInstaller file-compressor.spec --noconfirm
```

**Step 2: Run tests before packaging**

Run: `python -m pytest -q`

Expected: PASS.

**Step 3: Build executable**

Run: `powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1`

Expected: `dist/FileCompressor.exe` is created.

**Step 4: Commit**

```bash
git add file-compressor.spec scripts/build_exe.ps1
git commit -m "chore: add windows executable packaging"
```

---

## Task 14: Final Verification

**Files:**
- Modify: `README.md`

**Step 1: Update README with usage**

Add:

```markdown
## Run from source

```powershell
python -m pip install -e ".[dev]"
python -m file_compressor_app.main
```

## Build executable

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

## Supported formats

- `.xlsx`, `.xlsm`, `.pptx`, `.pptm`: direct ZIP-package image optimization.
- `.hwpx`: direct ZIP-package image optimization.
- `.pdf`: Ghostscript required.
- `.hwp`: Hancom Office required.
- `.xls`, `.ppt`: Microsoft Office required.
```

**Step 2: Run full test suite**

Run: `python -m pytest -q`

Expected: PASS.

**Step 3: Run app smoke test**

Run: `python -m file_compressor_app.main`

Expected: UI launches and allows files to be added.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document app usage"
```

---

## Notes for Execution

- Follow TDD for tasks 2 through 11.
- Do not overwrite user files.
- Do not make `.hwp` standalone parsing part of the first implementation.
- Keep dependency failures as skipped results instead of crashes.
- If PySide6 is unavailable, install project dependencies before UI work.
- If Ghostscript is not installed, PDF tests should still pass because missing-dependency behavior is tested without invoking Ghostscript.
