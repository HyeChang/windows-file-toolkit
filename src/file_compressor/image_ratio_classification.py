from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, replace
from pathlib import Path
import shutil
import struct
import threading

SUPPORTED_IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp",
    ".tif",
    ".tiff",
}

MATCH_CATEGORY = "조건 일치"
MISS_CATEGORY = "조건 미달"
READ_FAILED_CATEGORY = "읽기 실패"
NON_IMAGE_CATEGORY = "이미지 아님"
MATCH_OUTPUT_FOLDER = "조건충족"

_DIMENSION_CACHE: dict[str, tuple[int, int]] = {}


@dataclass(frozen=True)
class ImageRatioOptions:
    direction: str = "wide"
    threshold_ratio: float = 2.0
    reference_path: Path | None = None
    reference_multiplier: float = 1.0
    operation: str = "move"


@dataclass(frozen=True)
class ImageRatioPlan:
    source: Path
    target: Path
    category: str
    status: str
    width: int = 0
    height: int = 0
    ratio: float = 0.0
    threshold_ratio: float = 1.0
    direction: str = "wide"
    operation: str = "move"
    message: str = ""


def image_dimensions(path: Path) -> tuple[int, int]:
    path = Path(path)
    key = str(path)
    cached = _DIMENSION_CACHE.get(key)
    if cached is not None:
        return cached
    dimensions = _header_image_dimensions(path)
    _DIMENSION_CACHE[key] = dimensions
    return dimensions


def directional_ratio(width: int, height: int, direction: str) -> float:
    if width <= 0 or height <= 0:
        return 0.0
    if direction == "tall":
        return height / width
    return width / height


def effective_threshold_ratio(options: ImageRatioOptions) -> float:
    direction = _normalized_direction(options.direction)
    if options.reference_path is None:
        return max(1.0, float(options.threshold_ratio))
    try:
        width, height = image_dimensions(options.reference_path)
    except OSError:
        return max(1.0, float(options.threshold_ratio))
    reference_ratio = directional_ratio(width, height, direction)
    return max(0.01, reference_ratio * max(0.01, float(options.reference_multiplier)))


def build_image_ratio_classification_plan(
    paths: list[Path],
    output_root: Path | None,
    options: ImageRatioOptions,
) -> list[ImageRatioPlan]:
    direction = _normalized_direction(options.direction)
    operation = _normalized_operation(options.operation)
    threshold_ratio = effective_threshold_ratio(options)
    sources = [Path(path) for path in paths]
    dimension_results = _collect_dimension_results(sources, direction)
    occupied: set[Path] = set()
    plans: list[ImageRatioPlan] = []

    for source in sources:
        category = NON_IMAGE_CATEGORY
        width = 0
        height = 0
        ratio = 0.0
        status = "skipped"
        message = ""
        target = source

        if source.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            message = "Unsupported image type."
        else:
            result = dimension_results.get(source)
            if result is None:
                category = READ_FAILED_CATEGORY
                message = "Image dimensions could not be read."
            else:
                width, height, ratio, error = result
                if error:
                    category = READ_FAILED_CATEGORY
                    message = error
                elif ratio >= threshold_ratio:
                    category = MATCH_CATEGORY
                    status = "ready"
                    target = _unique_path(
                        _classification_target(source, output_root, category),
                        occupied,
                    )
                    occupied.add(target)
                else:
                    category = MISS_CATEGORY

        plans.append(
            ImageRatioPlan(
                source=source,
                target=target,
                category=category,
                status=status,
                width=width,
                height=height,
                ratio=ratio,
                threshold_ratio=threshold_ratio,
                direction=direction,
                operation=operation,
                message=message,
            )
        )

    return plans


def apply_image_ratio_classification_plan(plans: list[ImageRatioPlan]) -> list[ImageRatioPlan]:
    results: list[ImageRatioPlan | None] = [None] * len(plans)
    ready: list[tuple[int, ImageRatioPlan]] = []
    for index, plan in enumerate(plans):
        if plan.status == "unchanged":
            results[index] = replace(plan, status="unchanged", message="No change.")
            continue
        if plan.status != "ready":
            results[index] = plan
            continue
        ready.append((index, plan))

    if not ready:
        return [result if result is not None else plan for result, plan in zip(results, plans)]

    worker_count = min(4, len(ready))
    if worker_count <= 1:
        for index, plan in ready:
            results[index] = _apply_ready_plan(plan)
            _process_ui_events()
        return [result if result is not None else plan for result, plan in zip(results, plans)]

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(_apply_ready_plan, plan): index for index, plan in ready}
        pending = set(futures)
        while pending:
            done, pending = wait(pending, timeout=0.05, return_when=FIRST_COMPLETED)
            for future in done:
                results[futures[future]] = future.result()
            _process_ui_events()

    return [result if result is not None else plan for result, plan in zip(results, plans)]


def undo_image_ratio_classification_results(plans: list[ImageRatioPlan]) -> list[ImageRatioPlan]:
    results: list[ImageRatioPlan] = []
    for plan in plans:
        if plan.status != "completed":
            results.append(plan)
            continue
        try:
            if plan.operation == "copy":
                if not plan.target.exists():
                    results.append(replace(plan, status="failed", message="Copied file does not exist."))
                    continue
                plan.target.unlink()
            else:
                if not plan.target.exists():
                    results.append(replace(plan, status="failed", message="Moved file does not exist."))
                    continue
                if plan.source.exists():
                    results.append(replace(plan, status="failed", message="Original path already exists."))
                    continue
                plan.source.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(plan.target), str(plan.source))
            results.append(replace(plan, status="undone", message="Undo completed."))
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
    return results


def _collect_dimension_results(
    sources: list[Path],
    direction: str,
) -> dict[Path, tuple[int, int, float, str]]:
    candidates = [
        source
        for source in sources
        if source.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    ]
    if not candidates:
        return {}

    results: dict[Path, tuple[int, int, float, str]] = {}
    worker_count = min(16, len(candidates))
    if worker_count <= 1:
        for source in candidates:
            results[source] = _dimension_result(source, direction)
        return results

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(_dimension_result, source, direction): source for source in candidates}
        pending = set(futures)
        while pending:
            done, pending = wait(pending, timeout=0.05, return_when=FIRST_COMPLETED)
            for future in done:
                results[futures[future]] = future.result()
            _process_ui_events()
    return results


def _dimension_result(source: Path, direction: str) -> tuple[int, int, float, str]:
    try:
        width, height = image_dimensions(source)
        return width, height, directional_ratio(width, height, direction), ""
    except OSError as exc:
        return 0, 0, 0.0, str(exc)


def _apply_ready_plan(plan: ImageRatioPlan) -> ImageRatioPlan:
    if not plan.source.exists():
        return replace(plan, status="failed", message="Source file does not exist.")
    if plan.target.exists():
        return replace(plan, status="failed", message="Target file already exists.")
    try:
        plan.target.parent.mkdir(parents=True, exist_ok=True)
        if plan.operation == "copy":
            shutil.copy2(plan.source, plan.target)
            message = "Copied."
        else:
            shutil.move(str(plan.source), str(plan.target))
            message = "Moved."
        return replace(plan, status="completed", message=message)
    except OSError as exc:
        return replace(plan, status="failed", message=str(exc))


def _process_ui_events() -> None:
    if threading.current_thread() is not threading.main_thread():
        return
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return
    app = QApplication.instance()
    if app is not None:
        app.processEvents()


def _header_image_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as file:
        header = file.read(32)
        if header.startswith(b"\xff\xd8"):
            return _jpeg_dimensions(file)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            return struct.unpack(">II", header[16:24])
        if header[:6] in {b"GIF87a", b"GIF89a"} and len(header) >= 10:
            return struct.unpack("<HH", header[6:10])
        if header.startswith(b"BM") and len(header) >= 26:
            width, height = struct.unpack("<ii", header[18:26])
            return abs(width), abs(height)
        if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
            return _webp_dimensions(file, header)
        if header[:4] in {b"II*\x00", b"MM\x00*"}:
            return _tiff_dimensions(file, header)
    raise OSError("Unsupported or unreadable image header.")


def _jpeg_dimensions(file) -> tuple[int, int]:
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    no_payload_markers = {0x01, *range(0xD0, 0xD8)}
    file.seek(2)
    while True:
        byte = file.read(1)
        if not byte:
            break
        if byte != b"\xff":
            continue
        marker = file.read(1)
        while marker == b"\xff":
            marker = file.read(1)
        if not marker:
            break
        marker_value = marker[0]
        if marker_value in no_payload_markers:
            continue
        if marker_value in {0xD9, 0xDA}:
            break
        length_data = file.read(2)
        if len(length_data) != 2:
            break
        segment_length = struct.unpack(">H", length_data)[0]
        if segment_length < 2:
            break
        if marker_value in sof_markers:
            data = file.read(5)
            if len(data) != 5:
                break
            height, width = struct.unpack(">HH", data[1:5])
            return width, height
        file.seek(segment_length - 2, 1)
    raise OSError("JPEG dimensions could not be read.")


def _webp_dimensions(file, header: bytes) -> tuple[int, int]:
    chunk = header[12:16]
    size = struct.unpack("<I", header[16:20])[0] if len(header) >= 20 else 0
    payload = header[20:] + file.read(max(0, min(size, 32) - max(0, len(header) - 20)))
    if chunk == b"VP8X" and len(payload) >= 10:
        width = int.from_bytes(payload[4:7], "little") + 1
        height = int.from_bytes(payload[7:10], "little") + 1
        return width, height
    if chunk == b"VP8L" and len(payload) >= 5 and payload[0] == 0x2F:
        b1, b2, b3, b4 = payload[1:5]
        width = 1 + (((b2 & 0x3F) << 8) | b1)
        height = 1 + (((b4 & 0x0F) << 10) | (b3 << 2) | ((b2 & 0xC0) >> 6))
        return width, height
    if chunk == b"VP8 " and len(payload) >= 10 and payload[3:6] == b"\x9d\x01\x2a":
        width = struct.unpack("<H", payload[6:8])[0] & 0x3FFF
        height = struct.unpack("<H", payload[8:10])[0] & 0x3FFF
        return width, height
    raise OSError("WebP dimensions could not be read.")


def _tiff_dimensions(file, header: bytes) -> tuple[int, int]:
    endian = "<" if header[:2] == b"II" else ">"
    offset = struct.unpack(endian + "I", header[4:8])[0]
    file.seek(offset)
    count_data = file.read(2)
    if len(count_data) != 2:
        raise OSError("TIFF dimensions could not be read.")
    entry_count = struct.unpack(endian + "H", count_data)[0]
    width = 0
    height = 0
    for _ in range(min(entry_count, 512)):
        entry = file.read(12)
        if len(entry) != 12:
            break
        tag, value_type, value_count = struct.unpack(endian + "HHI", entry[:8])
        if tag not in {256, 257} or value_count < 1:
            continue
        value = _tiff_inline_value(entry[8:12], value_type, endian)
        if tag == 256:
            width = value
        else:
            height = value
        if width > 0 and height > 0:
            return width, height
    raise OSError("TIFF dimensions could not be read.")


def _tiff_inline_value(raw: bytes, value_type: int, endian: str) -> int:
    if value_type == 3:
        return struct.unpack(endian + "H", raw[:2])[0]
    if value_type == 4:
        return struct.unpack(endian + "I", raw)[0]
    return 0


def _classification_target(source: Path, output_root: Path | None, category: str) -> Path:
    if category == MATCH_CATEGORY:
        root = Path(output_root) if output_root is not None else _default_match_output_root(source)
        return root / source.name
    root = Path(output_root) if output_root is not None else source.parent / "이미지 비율 분류"
    return root / category / source.name


def _default_match_output_root(source: Path) -> Path:
    if source.parent.name == MATCH_OUTPUT_FOLDER:
        return source.parent
    return source.parent / MATCH_OUTPUT_FOLDER


def _unique_path(path: Path, occupied: set[Path]) -> Path:
    candidate = path
    counter = 2
    while candidate.exists() or candidate in occupied:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        counter += 1
    return candidate


def _normalized_direction(direction: str) -> str:
    if direction in {"wide", "tall"}:
        return direction
    return "wide"


def _normalized_operation(operation: str) -> str:
    if operation in {"move", "copy"}:
        return operation
    return "move"
