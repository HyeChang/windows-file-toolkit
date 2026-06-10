from __future__ import annotations

import ctypes
from dataclasses import dataclass, replace
from datetime import date, datetime, time as datetime_time
from difflib import SequenceMatcher
import os
import re
import shutil
from pathlib import Path


_INVALID_FILENAME_CHARS = '<>:"/\\|?*'
_CONTROL_CHARS = "".join(chr(value) for value in range(32))
_UNSAFE_TRANSLATION = str.maketrans("", "", _INVALID_FILENAME_CHARS + _CONTROL_CHARS)
_NAME_TOKEN_PATTERN = re.compile(r"[0-9A-Za-z가-힣]+")
_NAME_SIMILARITY_THRESHOLDS = {
    "loose": 0.25,
    "medium_loose": 0.35,
    "normal": 0.45,
    "medium_strict": 0.60,
    "strict": 0.75,
}
_EXISTING_FOLDER_SIMILARITY_THRESHOLDS = {
    "loose": 0.30,
    "medium_loose": 0.375,
    "normal": 0.45,
    "medium_strict": 0.55,
    "strict": 0.65,
}
_NAME_NOISE_TOKENS = {
    "final",
    "draft",
    "copy",
    "backup",
    "temp",
    "new",
    "old",
    "ver",
    "version",
    "최종",
    "초안",
    "검토",
    "검토본",
    "수정",
    "수정본",
    "복사",
    "복사본",
    "완료",
    "최신",
    "임시",
    "백업",
}
_EXISTING_FOLDER_NOISE_TOKENS = {
    "file",
    "files",
    "folder",
    "folders",
    "data",
    "파일",
    "폴더",
    "모음",
    "기타",
}


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
    date_fallback_source: str = "none"
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
    operation: str = "move"
    message: str = ""
    duplicate_action: str = "keep"
    folder_candidates: tuple[FolderMatchCandidate, ...] = ()


@dataclass(frozen=True)
class FolderMatchCandidate:
    path: Path
    score: float
    matched_terms: tuple[str, ...] = ()


@dataclass
class _NameSimilarityGroup:
    category: str
    tokens: set[str]
    name_key: str


@dataclass(frozen=True)
class _ExistingFolderCandidate:
    path: Path
    tokens: set[str]
    name_key: str


@dataclass(frozen=True)
class _ParsedDate:
    year: int | None
    month: int
    day: int | None
    precision: str

    def as_date(self) -> date | None:
        if self.year is None:
            return None
        return date(self.year, self.month, self.day or 1)


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
    if match is None:
        return None
    return match[0].as_date()


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

        target_stem = _build_target_stem(source, options, index)
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


def build_classification_plan(
    paths: list[Path],
    output_root: Path | None,
    *,
    operation: str = "move",
    strategy: str = "extension",
    sensitivity: str = "normal",
    auto_output_roots: dict[Path, Path] | None = None,
    duplicate_action: str = "keep",
    prefer_existing_similar_folders: bool = False,
    skip_single_file_category_folder: bool = False,
) -> list[ClassificationPlan]:
    fixed_output_root = Path(output_root) if output_root is not None else None
    auto_output_roots = {
        Path(source): Path(root)
        for source, root in (auto_output_roots or {}).items()
    }
    operation = operation if operation in {"move", "copy"} else "move"
    duplicate_action = duplicate_action if duplicate_action in {"keep", "delete"} else "keep"
    strategy = strategy if strategy in {"extension", "name_similarity"} else "extension"
    sensitivity = sensitivity if sensitivity in _NAME_SIMILARITY_THRESHOLDS else "normal"
    occupied: set[Path] = set()
    planned_targets: dict[Path, Path] = {}
    occupied_auto_roots: set[Path] = set()
    auto_roots: dict[Path, Path] = {}
    name_groups: list[_NameSimilarityGroup] = []
    existing_folder_cache: dict[Path, list[_ExistingFolderCandidate]] = {}
    plans: list[ClassificationPlan] = []
    should_skip_single_file_category_folder = skip_single_file_category_folder and len(paths) == 1
    for source in paths:
        source = Path(source)
        if strategy == "name_similarity":
            category = _classify_by_similar_file_name(source, name_groups, sensitivity)
        else:
            category = classify_file_category(source)
        if fixed_output_root is not None:
            target_root = fixed_output_root
        elif source in auto_output_roots:
            target_root = auto_output_roots[source]
        else:
            target_root = _auto_classification_output_root(
                source.parent,
                auto_roots,
                occupied_auto_roots,
            )
        existing_folder = None
        folder_candidates: tuple[FolderMatchCandidate, ...] = ()
        if prefer_existing_similar_folders and not should_skip_single_file_category_folder:
            existing_folder, folder_candidates = _find_similar_existing_folder(
                source,
                category,
                target_root,
                sensitivity,
                existing_folder_cache,
            )
        if existing_folder is not None:
            category = existing_folder.name
            target = existing_folder / source.name
        elif should_skip_single_file_category_folder and not folder_candidates:
            target = target_root / source.name
        else:
            target = target_root / category / source.name

        if not source.exists():
            plans.append(
                ClassificationPlan(
                    source=source,
                    target=target,
                    category=category,
                    status="skipped",
                    operation=operation,
                    message="Source file does not exist.",
                    duplicate_action=duplicate_action,
                    folder_candidates=folder_candidates,
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
                    operation=operation,
                    message="Folders cannot be moved as files.",
                    duplicate_action=duplicate_action,
                    folder_candidates=folder_candidates,
                )
            )
            continue

        if folder_candidates:
            status = "needs_choice"
        elif target == source:
            status = "unchanged"
        elif target.exists() and _files_have_same_content(source, target):
            status = "duplicate"
        elif target in planned_targets and _files_have_same_content(source, planned_targets[target]):
            status = "duplicate"
        else:
            target = _unique_path(target, occupied)
            status = "ready"

        if status == "ready":
            occupied.add(target)
            planned_targets[target] = source
        plans.append(
            ClassificationPlan(
                source=source,
                target=target,
                category=category,
                status=status,
                operation=operation,
                duplicate_action=duplicate_action,
                folder_candidates=folder_candidates,
            )
        )
    return plans


def _auto_classification_output_root(
    source_parent: Path,
    auto_roots: dict[Path, Path],
    occupied_auto_roots: set[Path],
) -> Path:
    source_parent = Path(source_parent)
    if source_parent not in auto_roots:
        auto_root = _unique_folder_path(source_parent / "정리", occupied_auto_roots)
        auto_roots[source_parent] = auto_root
        occupied_auto_roots.add(auto_root)
    return auto_roots[source_parent]


def _find_similar_existing_folder(
    source: Path,
    category: str,
    target_root: Path,
    sensitivity: str,
    existing_folder_cache: dict[Path, list[_ExistingFolderCandidate]],
) -> tuple[Path | None, tuple[FolderMatchCandidate, ...]]:
    target_root = Path(target_root)
    if target_root not in existing_folder_cache:
        existing_folder_cache[target_root] = _existing_folder_candidates(target_root)

    candidates = existing_folder_cache[target_root]
    if not candidates:
        return None, ()

    source_tokens, _, source_key = _filename_similarity_terms(source)
    category_tokens, _, category_key = _name_similarity_terms_from_text(category)
    threshold = _existing_folder_threshold(sensitivity)
    token_frequencies = _existing_folder_token_frequencies(candidates)
    scored_candidates: list[FolderMatchCandidate] = []
    for candidate in candidates:
        source_score = _existing_folder_similarity_score(
            source_tokens,
            source_key,
            candidate,
            token_frequencies,
            len(candidates),
        )
        category_score = _existing_folder_similarity_score(
            category_tokens,
            category_key,
            candidate,
            token_frequencies,
            len(candidates),
        )
        score = source_score if source_score.score >= category_score.score else category_score
        if score.score >= threshold:
            scored_candidates.append(score)

    if not scored_candidates:
        return None, ()

    scored_candidates.sort(key=lambda item: (-item.score, item.path.name.lower()))
    best_candidate = scored_candidates[0]
    second_candidate = scored_candidates[1] if len(scored_candidates) > 1 else None
    if _can_auto_select_existing_folder(best_candidate, second_candidate):
        return best_candidate.path, ()
    return None, tuple(scored_candidates[:5])


def _existing_folder_candidates(target_root: Path) -> list[_ExistingFolderCandidate]:
    try:
        children = sorted((child for child in Path(target_root).iterdir() if child.is_dir()), key=lambda path: path.name.lower())
    except OSError:
        return []

    candidates: list[_ExistingFolderCandidate] = []
    for child in children:
        tokens, _, name_key = _name_similarity_terms_from_text(child.name)
        tokens = _matchable_existing_folder_tokens(tokens)
        if tokens or name_key:
            candidates.append(_ExistingFolderCandidate(path=child, tokens=tokens, name_key=name_key))
    return candidates


def _existing_folder_threshold(sensitivity: str) -> float:
    return _EXISTING_FOLDER_SIMILARITY_THRESHOLDS.get(sensitivity, _EXISTING_FOLDER_SIMILARITY_THRESHOLDS["normal"])


def _can_auto_select_existing_folder(
    best_candidate: FolderMatchCandidate,
    second_candidate: FolderMatchCandidate | None,
) -> bool:
    if second_candidate is None:
        return True
    if len(best_candidate.matched_terms) >= len(second_candidate.matched_terms) + 2:
        return True
    return best_candidate.score - second_candidate.score >= 0.25


def _classify_by_similar_file_name(
    path: Path,
    groups: list[_NameSimilarityGroup],
    sensitivity: str,
) -> str:
    tokens, display_tokens, name_key = _filename_similarity_terms(path)
    if not tokens:
        return "Other"

    threshold = _NAME_SIMILARITY_THRESHOLDS[sensitivity]
    best_group: _NameSimilarityGroup | None = None
    best_score = 0.0
    for group in groups:
        score = _filename_similarity_score(tokens, name_key, group)
        if score > best_score:
            best_group = group
            best_score = score

    if best_group is not None and best_score >= threshold:
        best_group.tokens.update(tokens)
        return best_group.category

    category = _category_name_from_tokens(display_tokens)
    category = _unique_category_name(category, {group.category for group in groups})
    groups.append(_NameSimilarityGroup(category=category, tokens=set(tokens), name_key=name_key))
    return category


def _filename_similarity_terms(path: Path) -> tuple[set[str], list[str], str]:
    return _name_similarity_terms_from_text(Path(path).stem)


def _name_similarity_terms_from_text(text: str) -> tuple[set[str], list[str], str]:
    stem = _remove_dates_from_stem(text)
    tokens: set[str] = set()
    display_tokens: list[str] = []
    seen_display: set[str] = set()
    for token in _NAME_TOKEN_PATTERN.findall(stem):
        normalized = token.lower()
        if _is_noise_name_token(normalized):
            continue
        tokens.add(normalized)
        if normalized in seen_display:
            continue
        seen_display.add(normalized)
        display_tokens.append(token.upper() if token.isascii() and token.isalpha() else token)

    return tokens, display_tokens, "".join(display_tokens).lower()


def _remove_dates_from_stem(stem: str) -> str:
    cleaned = stem
    while True:
        match = _find_date_match(cleaned)
        if match is None:
            return cleaned
        cleaned = _remove_date_match(cleaned, match[1])


def _is_noise_name_token(token: str) -> bool:
    if token in _NAME_NOISE_TOKENS:
        return True
    if token.isdigit():
        return True
    if re.fullmatch(r"v?\d+(?:\.\d+)*", token):
        return True
    return False


def _category_name_from_tokens(display_tokens: list[str]) -> str:
    category = clean_file_stem(" ".join(display_tokens), clean_spaces=True, clean_special=True)
    if not category:
        return "Other"
    return category[:80].rstrip()


def _filename_similarity_score(
    tokens: set[str],
    name_key: str,
    group: _NameSimilarityGroup,
) -> float:
    union = tokens | group.tokens
    token_score = len(tokens & group.tokens) / len(union) if union else 0.0
    sequence_score = SequenceMatcher(None, name_key, group.name_key).ratio() if name_key and group.name_key else 0.0
    return max(token_score, sequence_score)


def _existing_folder_similarity_score(
    tokens: set[str],
    name_key: str,
    candidate: _ExistingFolderCandidate,
    token_frequencies: dict[str, int],
    folder_count: int,
) -> FolderMatchCandidate:
    matchable_tokens = _matchable_existing_folder_tokens(tokens)
    if not matchable_tokens or not candidate.tokens:
        return FolderMatchCandidate(path=candidate.path, score=0.0)

    matched_terms = _existing_folder_matched_terms(matchable_tokens, candidate.tokens)
    if not matched_terms:
        return FolderMatchCandidate(path=candidate.path, score=0.0)

    matched_weight = sum(_existing_folder_token_weight(term, token_frequencies, folder_count) for term in matched_terms)
    input_weight = sum(_existing_folder_token_weight(token, token_frequencies, folder_count) for token in matchable_tokens)
    candidate_weight = sum(_existing_folder_token_weight(token, token_frequencies, folder_count) for token in candidate.tokens)
    denominator = max(min(input_weight, candidate_weight), 0.001)
    coverage_score = min(1.0, matched_weight / denominator)
    sequence_score = SequenceMatcher(None, name_key, candidate.name_key).ratio() if name_key and candidate.name_key else 0.0
    score = max(coverage_score, sequence_score * 0.35)
    return FolderMatchCandidate(
        path=candidate.path,
        score=round(score, 6),
        matched_terms=tuple(sorted(matched_terms)),
    )


def _existing_folder_token_frequencies(candidates: list[_ExistingFolderCandidate]) -> dict[str, int]:
    frequencies: dict[str, int] = {}
    for candidate in candidates:
        for token in candidate.tokens:
            frequencies[token] = sum(
                1
                for other in candidates
                if any(_tokens_match_for_existing_folder(token, other_token) for other_token in other.tokens)
            )
    return frequencies


def _existing_folder_token_weight(token: str, token_frequencies: dict[str, int], folder_count: int) -> float:
    if folder_count <= 1:
        return 1.0
    frequency = max(1, token_frequencies.get(token, 1))
    return 1.0 + ((folder_count - frequency) / folder_count)


def _existing_folder_matched_terms(tokens: set[str], folder_tokens: set[str]) -> set[str]:
    matched_terms: set[str] = set()
    for token in tokens:
        for folder_token in folder_tokens:
            if _tokens_match_for_existing_folder(token, folder_token):
                matched_terms.add(folder_token if len(folder_token) <= len(token) else token)
    return matched_terms


def _tokens_match_for_existing_folder(left: str, right: str) -> bool:
    if left == right:
        return True
    shorter, longer = sorted((left, right), key=len)
    if not _is_partial_existing_folder_token(shorter):
        return False
    return shorter in longer


def _is_partial_existing_folder_token(token: str) -> bool:
    if token.isascii():
        return len(token) >= 4
    return len(token) >= 2


def _matchable_existing_folder_tokens(tokens: set[str]) -> set[str]:
    return {token for token in tokens if _is_matchable_existing_folder_token(token)}


def _is_matchable_existing_folder_token(token: str) -> bool:
    if token in _EXISTING_FOLDER_NOISE_TOKENS:
        return False
    if token.isascii():
        return len(token) >= 3
    return len(token) >= 2


def _is_strong_existing_folder_token(token: str) -> bool:
    if token.isascii():
        return len(token) >= 4
    return len(token) >= 3


def _unique_category_name(category: str, occupied: set[str]) -> str:
    if category not in occupied:
        return category

    counter = 2
    while True:
        candidate = f"{category}_{counter}"
        if candidate not in occupied:
            return candidate
        counter += 1


def apply_classification_plan(plans: list[ClassificationPlan]) -> list[ClassificationPlan]:
    results: list[ClassificationPlan] = []
    for plan in plans:
        if plan.status == "unchanged":
            results.append(replace(plan, status="unchanged", message="No change."))
            continue
        if plan.status == "duplicate" and plan.duplicate_action == "delete":
            results.append(_delete_duplicate_classification_source(plan))
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
            if plan.operation == "copy":
                shutil.copy2(plan.source, plan.target)
            else:
                shutil.move(str(plan.source), str(plan.target))
        except OSError as exc:
            results.append(replace(plan, status="failed", message=str(exc)))
        else:
            message = "Copied." if plan.operation == "copy" else "Moved."
            results.append(replace(plan, status="completed", message=message))
    return results


def _delete_duplicate_classification_source(plan: ClassificationPlan) -> ClassificationPlan:
    if not plan.source.exists():
        return replace(plan, status="failed", message="Source file does not exist.")
    if not plan.target.exists():
        return replace(plan, status="failed", message="Duplicate target does not exist.")
    if not _files_have_same_content(plan.source, plan.target):
        return replace(plan, status="failed", message="Duplicate target content changed.")
    try:
        plan.source.unlink()
    except OSError as exc:
        return replace(plan, status="failed", message=str(exc))
    return replace(plan, status="duplicate_deleted", message="Duplicate source deleted.")


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
        if plan.operation == "copy":
            if not plan.target.exists():
                results.append(replace(plan, status="failed", message="Copied file does not exist."))
                continue
            try:
                plan.target.unlink()
            except OSError as exc:
                results.append(replace(plan, status="failed", message=str(exc)))
            else:
                results.append(replace(plan, status="undone", message="Undo completed."))
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


def _build_target_stem(source: Path, options: RenameOptions, index: int) -> str:
    stem = source.stem
    if options.find_text:
        stem = stem.replace(options.find_text, options.replace_text)

    date_value: _ParsedDate | None = None
    if options.date_format != "none":
        date_match = _find_date_match(stem)
        if date_match:
            date_value, match = date_match
            stem = _remove_date_match(stem, match)
        else:
            date_value = _date_from_file_timestamp(source, options.date_fallback_source)

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


def _format_stem_with_date(stem: str, value: _ParsedDate, mode: str) -> str:
    if value.year is None:
        compact = f"{value.month:02d}{value.day or 1:02d}"
        short_compact = compact
        dashed = f"{value.month:02d}-{value.day or 1:02d}"
        underscored = f"{value.month:02d}_{value.day or 1:02d}"
    elif value.precision == "month":
        compact = f"{value.year:04d}{value.month:02d}"
        short_compact = f"{value.year % 100:02d}{value.month:02d}"
        dashed = f"{value.year:04d}-{value.month:02d}"
        underscored = f"{value.year:04d}_{value.month:02d}"
    else:
        compact = f"{value.year:04d}{value.month:02d}{value.day or 1:02d}"
        short_compact = f"{value.year % 100:02d}{value.month:02d}{value.day or 1:02d}"
        dashed = f"{value.year:04d}-{value.month:02d}-{value.day or 1:02d}"
        underscored = f"{value.year:04d}_{value.month:02d}_{value.day or 1:02d}"
    if mode == "prefix_dash":
        return _join_date_prefix(dashed, stem)
    if mode == "prefix_compact":
        return _join_date_prefix(compact, stem)
    if mode == "prefix_short_compact":
        return _join_date_prefix(short_compact, stem)
    if mode == "prefix_underscore":
        return _join_date_prefix(underscored, stem)
    if mode == "suffix_dash":
        return _join_date_suffix(stem, dashed)
    if mode == "suffix_compact":
        return _join_date_suffix(stem, compact)
    if mode == "suffix_short_compact":
        return _join_date_suffix(stem, short_compact)
    if mode == "suffix_underscore":
        return _join_date_suffix(stem, underscored)
    return stem


def _join_date_prefix(date_text: str, stem: str) -> str:
    return f"{date_text}_{stem}" if stem else date_text


def _join_date_suffix(stem: str, date_text: str) -> str:
    return f"{stem}_{date_text}" if stem else date_text


def _find_date_match(stem: str) -> tuple[_ParsedDate, re.Match[str]] | None:
    for pattern in _date_patterns():
        for match in pattern.finditer(stem):
            if _is_version_number_date_match(stem, match):
                continue
            parsed = _date_from_match(match)
            if parsed is not None:
                return parsed
    return None


def _is_version_number_date_match(stem: str, match: re.Match[str]) -> bool:
    before = stem[: match.start()].rstrip(" \t_-.")
    if not before:
        return False
    if re.search(r"(?i)(?:^|[\s_\-.])(?:v|ver|version)$", before):
        return True
    return re.search(r"버전$", before) is not None


def _date_patterns() -> list[re.Pattern[str]]:
    separated_time = r"(?:[\s_T-]+(?P<hour>\d{1,2})(?:[:\s_-]?(?P<minute>\d{2}))?(?:[:\s_-]?(?P<second>\d{2}))?(?:[.,]\d{1,6})?)?"
    korean_time = r"(?:[\s_]+(?:(?:오전|오후|AM|PM|am|pm)[\s_]*)?(?P<hour>\d{1,2})(?:[:\s_-]?(?P<minute>\d{1,2}))?(?:[:\s_-]?(?P<second>\d{1,2}))?(?:[.,]\d{1,6})?)?"
    compact_time = r"(?:[\s_T-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})?(?P<fraction>\d{1,6})?)?"
    return [
        re.compile(rf"(?<!\d)(?P<year>\d{{4}})년[\s_]*(?P<month>\d{{1,2}})월[\s_]*(?P<day>\d{{1,2}})일{korean_time}"),
        re.compile(rf"(?<!\d)(?P<year>\d{{4}})[-._](?P<month>\d{{1,2}})[-._](?P<day>\d{{1,2}}){separated_time}(?!\d)"),
        re.compile(rf"(?<!\d)(?P<year>\d{{4}})(?P<month>\d{{2}})(?P<day>\d{{2}}){compact_time}(?!\d)"),
        re.compile(rf"(?<!\d)(?P<year>\d{{2}})(?P<month>\d{{2}})(?P<day>\d{{2}}){compact_time}(?!\d)"),
        re.compile(r"(?<!\d)(?P<year>\d{4})년[\s_]*(?P<month>\d{1,2})월"),
        re.compile(r"(?<!\d)(?P<year>\d{2})년[\s_]*(?P<month>\d{1,2})월"),
        re.compile(r"(?<![\dA-Za-z가-힣])(?P<month>0?[1-9]|1[0-2])[-./](?P<day>0?[1-9]|[12]\d|3[01])(?![\dA-Za-z가-힣])"),
        re.compile(r"(?<![\dA-Za-z가-힣])(?P<month>0[1-9]|1[0-2])(?P<day>0[1-9]|[12]\d|3[01])(?![\dA-Za-z가-힣])"),
    ]


def _date_from_file_timestamp(path: Path, source: str) -> _ParsedDate | None:
    if source not in {"created", "modified"}:
        return None
    try:
        timestamps = get_file_timestamps(path)
    except OSError:
        return None

    timestamp = timestamps.created if source == "created" else timestamps.modified
    value = datetime.fromtimestamp(timestamp)
    return _ParsedDate(year=value.year, month=value.month, day=value.day, precision="day")


def _date_from_match(match: re.Match[str]) -> tuple[_ParsedDate, re.Match[str]] | None:
    year_text = match.groupdict().get("year")
    year: int | None = None
    if year_text:
        year = int(year_text)
        if len(year_text) == 2:
            year += 2000 if year <= 69 else 1900
    day_text = match.groupdict().get("day")
    day = int(day_text) if day_text else 1
    if year is None:
        precision = "month_day"
    else:
        precision = "day" if day_text else "month"

    try:
        if year is not None:
            date(year, int(match.group("month")), day)
        else:
            date(2000, int(match.group("month")), day)
    except ValueError:
        return None
    return _ParsedDate(year=year, month=int(match.group("month")), day=day, precision=precision), match


def _remove_date_match(stem: str, match: re.Match[str]) -> str:
    without_date = f"{stem[: match.start()]}{stem[match.end() :]}"
    without_date = re.sub(r"\(\s*\)|\[\s*\]|\{\s*\}", "", without_date)
    without_date = re.sub(r"^[\s_\-.,]+", "", without_date)
    without_date = re.sub(r"[\s_\-.,]+$", "", without_date)
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


def _files_have_same_content(left: Path, right: Path) -> bool:
    left = Path(left)
    right = Path(right)
    try:
        if not left.is_file() or not right.is_file():
            return False
        if left.stat().st_size != right.stat().st_size:
            return False
        with left.open("rb") as left_file, right.open("rb") as right_file:
            while True:
                left_chunk = left_file.read(1024 * 1024)
                right_chunk = right_file.read(1024 * 1024)
                if left_chunk != right_chunk:
                    return False
                if not left_chunk:
                    return True
    except OSError:
        return False


def _unique_folder_path(path: Path, occupied: set[Path]) -> Path:
    candidate = path
    counter = 1
    while candidate.exists() or candidate in occupied:
        candidate = path.with_name(f"{path.name}_{counter}")
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
