from __future__ import annotations

import ctypes
from dataclasses import dataclass, replace
from datetime import date, datetime, time as datetime_time
import os
import re
import shutil
from pathlib import Path


_INVALID_FILENAME_CHARS = '<>:"/\\|?*'
_CONTROL_CHARS = "".join(chr(value) for value in range(32))
_UNSAFE_TRANSLATION = str.maketrans("", "", _INVALID_FILENAME_CHARS + _CONTROL_CHARS)


@dataclass(frozen=True)
class RenameOptions:
    prefix: str = ""
    suffix: str = ""
    find_text: str = ""
    replace_text: str = ""
    clean_spaces: bool = False
    clean_special: bool = False
    number_files: bool = False
    number_start: int = 1
    date_format: str = "none"
    preserve_modified_time: bool = True


@dataclass(frozen=True)
class RenamePlan:
    source: Path
    target: Path
    status: str
    message: str = ""
    preserve_modified_time: bool = True


@dataclass(frozen=True)
class ClassificationPlan:
    source: Path
    target: Path
    category: str
    status: str
    message: str = ""


@dataclass(frozen=True)
class FileTimestamps:
    created: float
    modified: float


@dataclass(frozen=True)
class DateChangePlan:
    source: Path
    target_timestamps: FileTimestamps
    status: str
    message: str = ""
    original_timestamps: FileTimestamps | None = None


def clean_file_stem(stem: str, *, clean_spaces: bool = True, clean_special: bool = True) -> str:
    if clean_special:
        stem = stem.translate(_UNSAFE_TRANSLATION)
    if clean_spaces:
        stem = re.sub(r"\s+", " ", stem)
    return stem.strip().rstrip(".")


def extract_date_from_name(name: str) -> date | None:
    match = _find_date_match(Path(name).stem)
    return match[0] if match else None


def build_rename_plan(paths: list[Path], options: RenameOptions) -> list[RenamePlan]:
    occupied: set[Path] = set()
    plans: list[RenamePlan] = []
    for index, source in enumerate(paths):
        source = Path(source)
        if not source.exists():
            plans.append(
                RenamePlan(
                    source=source,
                    target=source,
                    status="skipped",
                    message="Source file does not exist.",
                    preserve_modified_time=options.preserve_modified_time,
                )
            )
            continue

        target_stem = _build_target_stem(source.stem, options, index)
        if not target_stem:
            target_stem = source.stem
        target = source.with_name(f"{target_stem}{source.suffix}")

        if target == source:
            status = "unchanged"
        else:
            target = _unique_path(target, occupied)
            status = "ready"

        occupied.add(target)
        plans.append(
            RenamePlan(
                source=source,
                target=target,
                status=status,
                preserve_modified_time=options.preserve_modified_time,
            )
        )
    return plans


def apply_rename_plan(plans: list[RenamePlan]) -> list[RenamePlan]:
    results: list[RenamePlan] = []
    for plan in plans:
        if plan.status == "unchanged":
            results.append(replace(plan, status="unchanged", message="No change."))
            continue
        if plan.status != "ready":
            results.append(plan)
            continue
        if not plan.source.exists():
            results.append(replace(plan, status="failed", message="Source file does not exist."))
            continue
        if plan.target.exists():
            results.append(replace(plan, status="failed", message="Target file already exists."))
            continue

        try:
            original_stat = plan.source.stat()
            plan.source.rename(plan.target)
            if plan.preserve_modified_time:
                os.utime(plan.target, (original_stat.st_atime, original_stat.st_mtime))
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
        else:
            results.append(replace(plan, status="completed", message="Renamed."))
    return results


def classify_file_category(path: Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return "PDF"
    if suffix in {".xlsx", ".xlsm", ".xls", ".csv"}:
        return "Excel"
    if suffix in {".pptx", ".pptm", ".ppt"}:
        return "PowerPoint"
    if suffix in {".hwp", ".hwpx"}:
        return "HWP"
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".heic"}:
        return "Images"
    if suffix in {".doc", ".docx", ".txt", ".rtf", ".odt", ".md"}:
        return "Documents"
    if suffix in {".zip", ".7z", ".rar", ".tar", ".gz"}:
        return "Archives"
    return "Other"


def build_classification_plan(paths: list[Path], output_root: Path) -> list[ClassificationPlan]:
    output_root = Path(output_root)
    occupied: set[Path] = set()
    plans: list[ClassificationPlan] = []
    for source in paths:
        source = Path(source)
        category = classify_file_category(source)
        target = output_root / category / source.name

        if not source.exists():
            plans.append(
                ClassificationPlan(
                    source=source,
                    target=target,
                    category=category,
                    status="skipped",
                    message="Source file does not exist.",
                )
            )
            continue
        if source.is_dir():
            plans.append(
                ClassificationPlan(
                    source=source,
                    target=target,
                    category=category,
                    status="skipped",
                    message="Folders cannot be moved as files.",
                )
            )
            continue

        if target == source:
            status = "unchanged"
        else:
            target = _unique_path(target, occupied)
            status = "ready"

        occupied.add(target)
        plans.append(ClassificationPlan(source=source, target=target, category=category, status=status))
    return plans


def apply_classification_plan(plans: list[ClassificationPlan]) -> list[ClassificationPlan]:
    results: list[ClassificationPlan] = []
    for plan in plans:
        if plan.status == "unchanged":
            results.append(replace(plan, status="unchanged", message="No change."))
            continue
        if plan.status != "ready":
            results.append(plan)
            continue
        if not plan.source.exists():
            results.append(replace(plan, status="failed", message="Source file does not exist."))
            continue
        if plan.target.exists():
            results.append(replace(plan, status="failed", message="Target file already exists."))
            continue

        try:
            plan.target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(plan.source), str(plan.target))
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
        else:
            results.append(replace(plan, status="completed", message="Moved."))
    return results


def get_file_timestamps(path: Path) -> FileTimestamps:
    stat = Path(path).stat()
    return FileTimestamps(created=stat.st_ctime, modified=stat.st_mtime)


def set_file_timestamps(path: Path, *, created: float | None = None, modified: float | None = None):
    path = Path(path)
    if os.name == "nt":
        _set_windows_file_timestamps(path, created=created, modified=modified)
        return

    if created is not None:
        raise OSError("Creation time changes require Windows.")
    if modified is not None:
        current = path.stat()
        os.utime(path, (current.st_atime, modified))


def build_date_change_plan(
    paths: list[Path],
    *,
    created_timestamp: float | None = None,
    modified_timestamp: float | None = None,
    from_filename: bool = False,
    use_now: bool = False,
    now_timestamp: float | None = None,
    change_created: bool = True,
    change_modified: bool = True,
) -> list[DateChangePlan]:
    plans: list[DateChangePlan] = []
    for source in paths:
        source = Path(source)
        if not source.exists():
            plans.append(
                DateChangePlan(
                    source=source,
                    target_timestamps=FileTimestamps(0, 0),
                    status="skipped",
                    message="Source file does not exist.",
                )
            )
            continue

        current = get_file_timestamps(source)
        target_timestamp: float | None = None
        if from_filename:
            extracted = extract_date_from_name(source.name)
            if extracted is None:
                plans.append(
                    DateChangePlan(
                        source=source,
                        target_timestamps=current,
                        status="skipped",
                        message="No date found in file name.",
                    )
                )
                continue
            target_timestamp = _timestamp_from_date(extracted)
        elif use_now:
            target_timestamp = now_timestamp if now_timestamp is not None else datetime.now().timestamp()

        target_created = current.created
        target_modified = current.modified
        if change_created:
            target_created = _selected_timestamp(created_timestamp, target_timestamp, current.created)
        if change_modified:
            target_modified = _selected_timestamp(modified_timestamp, target_timestamp, current.modified)

        plans.append(
            DateChangePlan(
                source=source,
                target_timestamps=FileTimestamps(target_created, target_modified),
                status="ready",
            )
        )
    return plans


def apply_date_change_plan(plans: list[DateChangePlan]) -> list[DateChangePlan]:
    results: list[DateChangePlan] = []
    for plan in plans:
        if plan.status != "ready":
            results.append(plan)
            continue
        if not plan.source.exists():
            results.append(replace(plan, status="failed", message="Source file does not exist."))
            continue

        try:
            original = get_file_timestamps(plan.source)
            set_file_timestamps(
                plan.source,
                created=plan.target_timestamps.created,
                modified=plan.target_timestamps.modified,
            )
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
        else:
            results.append(
                replace(
                    plan,
                    status="completed",
                    message="Dates changed.",
                    original_timestamps=original,
                )
            )
    return results


def undo_rename_results(plans: list[RenamePlan]) -> list[RenamePlan]:
    results: list[RenamePlan] = []
    for plan in plans:
        if plan.status != "completed":
            results.append(plan)
            continue
        if not plan.target.exists():
            results.append(replace(plan, status="failed", message="Changed file does not exist."))
            continue
        if plan.source.exists():
            results.append(replace(plan, status="failed", message="Original path already exists."))
            continue
        try:
            plan.target.rename(plan.source)
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
        else:
            results.append(replace(plan, status="undone", message="Undo completed."))
    return results


def undo_classification_results(plans: list[ClassificationPlan]) -> list[ClassificationPlan]:
    results: list[ClassificationPlan] = []
    for plan in plans:
        if plan.status != "completed":
            results.append(plan)
            continue
        if not plan.target.exists():
            results.append(replace(plan, status="failed", message="Moved file does not exist."))
            continue
        if plan.source.exists():
            results.append(replace(plan, status="failed", message="Original path already exists."))
            continue
        try:
            plan.source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(plan.target), str(plan.source))
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
        else:
            results.append(replace(plan, status="undone", message="Undo completed."))
    return results


def undo_date_change_results(plans: list[DateChangePlan]) -> list[DateChangePlan]:
    results: list[DateChangePlan] = []
    for plan in plans:
        if plan.status != "completed":
            results.append(plan)
            continue
        if plan.original_timestamps is None:
            results.append(replace(plan, status="failed", message="Original timestamps are missing."))
            continue
        if not plan.source.exists():
            results.append(replace(plan, status="failed", message="Source file does not exist."))
            continue

        try:
            set_file_timestamps(
                plan.source,
                created=plan.original_timestamps.created,
                modified=plan.original_timestamps.modified,
            )
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
        else:
            results.append(replace(plan, status="undone", message="Undo completed."))
    return results


def _build_target_stem(source_stem: str, options: RenameOptions, index: int) -> str:
    stem = source_stem
    if options.find_text:
        stem = stem.replace(options.find_text, options.replace_text)

    date_value: date | None = None
    if options.date_format != "none":
        date_match = _find_date_match(stem)
        if date_match:
            date_value, match = date_match
            stem = _remove_date_match(stem, match)

    if options.clean_spaces or options.clean_special:
        stem = clean_file_stem(
            stem,
            clean_spaces=options.clean_spaces,
            clean_special=options.clean_special,
        )
    else:
        stem = stem.strip().rstrip(".")

    stem = f"{options.prefix}{stem}{options.suffix}"
    if options.number_files:
        number = options.number_start + index
        stem = f"{number:03d}_{stem}"

    if date_value is not None:
        stem = _format_stem_with_date(stem, date_value, options.date_format)

    return clean_file_stem(stem, clean_spaces=True, clean_special=True)


def _format_stem_with_date(stem: str, value: date, mode: str) -> str:
    compact = value.strftime("%Y%m%d")
    dashed = value.strftime("%Y-%m-%d")
    if mode == "prefix_dash":
        return f"{dashed}_{stem}"
    if mode == "prefix_compact":
        return f"{compact}_{stem}"
    if mode == "suffix_dash":
        return f"{stem}_{dashed}"
    if mode == "suffix_compact":
        return f"{stem}_{compact}"
    return stem


def _find_date_match(stem: str) -> tuple[date, re.Match[str]] | None:
    for pattern in _date_patterns():
        match = pattern.search(stem)
        if not match:
            continue
        parsed = _date_from_match(match)
        if parsed is not None:
            return parsed, match
    return None


def _date_patterns() -> list[re.Pattern[str]]:
    return [
        re.compile(r"(?<!\d)(?P<year>\d{4})년\s*(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일"),
        re.compile(r"(?<!\d)(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})(?!\d)"),
        re.compile(r"(?<!\d)(?P<year>\d{4})[-._](?P<month>\d{1,2})[-._](?P<day>\d{1,2})(?!\d)"),
        re.compile(r"(?<!\d)(?P<year>\d{2})(?P<month>\d{2})(?P<day>\d{2})(?!\d)"),
    ]


def _date_from_match(match: re.Match[str]) -> date | None:
    year_text = match.group("year")
    year = int(year_text)
    if len(year_text) == 2:
        year += 2000 if year <= 69 else 1900

    try:
        return date(year, int(match.group("month")), int(match.group("day")))
    except ValueError:
        return None


def _remove_date_match(stem: str, match: re.Match[str]) -> str:
    without_date = f"{stem[: match.start()]}{stem[match.end() :]}"
    without_date = re.sub(r"^[\s_\-.,()\[\]]+", "", without_date)
    without_date = re.sub(r"[\s_\-.,()\[\]]+$", "", without_date)
    without_date = re.sub(r"\s{2,}", " ", without_date)
    without_date = re.sub(r"_{2,}", "_", without_date)
    without_date = re.sub(r"-{2,}", "-", without_date)
    return without_date.strip()


def _unique_path(path: Path, occupied: set[Path]) -> Path:
    candidate = path
    counter = 2
    while candidate.exists() or candidate in occupied:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        counter += 1
    return candidate


def _selected_timestamp(manual: float | None, shared: float | None, current: float) -> float:
    if shared is not None:
        return shared
    if manual is not None:
        return manual
    return current


def _timestamp_from_date(value: date) -> float:
    return datetime.combine(value, datetime_time()).timestamp()


def _set_windows_file_timestamps(path: Path, *, created: float | None, modified: float | None):
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = ctypes.c_void_p
    kernel32.SetFileTime.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(_FILETIME),
        ctypes.POINTER(_FILETIME),
        ctypes.POINTER(_FILETIME),
    ]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    file_write_attributes = 0x0100
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    file_share_delete = 0x00000004
    open_existing = 3
    file_flag_backup_semantics = 0x02000000
    invalid_handle_value = ctypes.c_void_p(-1).value

    handle = kernel32.CreateFileW(
        str(path),
        file_write_attributes,
        file_share_read | file_share_write | file_share_delete,
        None,
        open_existing,
        file_flag_backup_semantics if path.is_dir() else 0,
        None,
    )
    if handle == invalid_handle_value:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        creation_time = _timestamp_to_filetime(created)
        last_write_time = _timestamp_to_filetime(modified)
        creation_pointer = ctypes.byref(creation_time) if creation_time is not None else None
        last_write_pointer = ctypes.byref(last_write_time) if last_write_time is not None else None
        if not kernel32.SetFileTime(handle, creation_pointer, None, last_write_pointer):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel32.CloseHandle(handle)


class _FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", ctypes.c_uint32),
        ("dwHighDateTime", ctypes.c_uint32),
    ]


def _timestamp_to_filetime(timestamp: float | None) -> _FILETIME | None:
    if timestamp is None:
        return None

    intervals = int((timestamp + 11644473600) * 10_000_000)
    return _FILETIME(intervals & 0xFFFFFFFF, intervals >> 32)
