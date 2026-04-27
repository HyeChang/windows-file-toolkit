from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
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
