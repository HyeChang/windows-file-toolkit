from datetime import date, datetime
import os
from pathlib import Path
import shutil

from file_compressor.file_tools import (
    apply_classification_plan,
    apply_date_change_plan,
    RenameOptions,
    apply_rename_plan,
    build_rename_plan,
    build_classification_plan,
    build_date_change_plan,
    classify_file_category,
    clean_file_stem,
    extract_date_from_name,
    get_file_timestamps,
    set_file_timestamps,
    undo_classification_results,
    undo_date_change_results,
    undo_rename_results,
)


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def test_extract_date_from_supported_file_names():
    assert extract_date_from_name("회의록_20260427.pdf") == date(2026, 4, 27)
    assert extract_date_from_name("회의록_2026-04-27.pdf") == date(2026, 4, 27)
    assert extract_date_from_name("회의록_2026.04.27.pdf") == date(2026, 4, 27)
    assert extract_date_from_name("회의록_2026_04_27.pdf") == date(2026, 4, 27)
    assert extract_date_from_name("회의록_2026년 4월 7일.pdf") == date(2026, 4, 7)
    assert extract_date_from_name("회의록_260427.pdf") == date(2026, 4, 27)


def test_rename_plan_normalizes_date_to_file_name_suffix_compact():
    workdir = case_dir("rename-date-suffix-compact")
    source = workdir / "2026.04.27_회의록 초안.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_rename_plan([source], RenameOptions(date_format="suffix_compact"))

    assert plan.status == "ready"
    assert plan.target == workdir / "회의록 초안_20260427.pdf"


def test_rename_plan_cleans_spaces_and_unsafe_characters():
    assert clean_file_stem("  보고서   최종<>:\"/\\|?*  ") == "보고서 최종"

    workdir = case_dir("rename-clean-spaces")
    source = workdir / "  보고서   최종  .pdf"
    source.write_bytes(b"pdf")

    [plan] = build_rename_plan([source], RenameOptions(clean_spaces=True))

    assert plan.target == workdir / "보고서 최종.pdf"


def test_rename_plan_avoids_existing_and_planned_collisions():
    workdir = case_dir("rename-collisions")
    first = workdir / "2026-04-27 보고서.pdf"
    second = workdir / "2026.04.27 보고서.pdf"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    (workdir / "보고서_20260427.pdf").write_bytes(b"exists")

    plans = build_rename_plan(
        [first, second],
        RenameOptions(date_format="suffix_compact", clean_spaces=True),
    )

    assert plans[0].target == workdir / "보고서_20260427_2.pdf"
    assert plans[1].target == workdir / "보고서_20260427_3.pdf"


def test_apply_rename_plan_preserves_modified_time_by_default():
    workdir = case_dir("rename-preserve-mtime")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")
    original_mtime = 1_700_000_000
    os.utime(source, (original_mtime, original_mtime))

    [plan] = build_rename_plan([source], RenameOptions(suffix="_완료"))
    results = apply_rename_plan([plan])

    assert results[0].status == "completed"
    assert not source.exists()
    assert plan.target.exists()
    assert abs(plan.target.stat().st_mtime - original_mtime) < 1


def test_classify_file_category_maps_common_extensions():
    assert classify_file_category(Path("report.pdf")) == "PDF"
    assert classify_file_category(Path("budget.xlsx")) == "Excel"
    assert classify_file_category(Path("legacy.xls")) == "Excel"
    assert classify_file_category(Path("deck.pptx")) == "PowerPoint"
    assert classify_file_category(Path("draft.hwp")) == "HWP"
    assert classify_file_category(Path("image.png")) == "Images"
    assert classify_file_category(Path("memo.docx")) == "Documents"
    assert classify_file_category(Path("bundle.zip")) == "Archives"
    assert classify_file_category(Path("unknown.bin")) == "Other"


def test_classification_plan_groups_files_under_output_folder_and_avoids_collisions():
    workdir = case_dir("classification-plan")
    source_a = workdir / "a" / "report.pdf"
    source_b = workdir / "b" / "report.pdf"
    output_root = workdir / "sorted"
    source_a.parent.mkdir()
    source_b.parent.mkdir()
    (output_root / "PDF").mkdir(parents=True)
    source_a.write_bytes(b"a")
    source_b.write_bytes(b"b")
    (output_root / "PDF" / "report.pdf").write_bytes(b"exists")

    plans = build_classification_plan([source_a, source_b], output_root)

    assert plans[0].category == "PDF"
    assert plans[0].target == output_root / "PDF" / "report_2.pdf"
    assert plans[1].target == output_root / "PDF" / "report_3.pdf"


def test_apply_classification_plan_moves_files_to_category_folder():
    workdir = case_dir("classification-apply")
    source = workdir / "보고서.pdf"
    output_root = workdir / "sorted"
    source.write_bytes(b"pdf")

    [plan] = build_classification_plan([source], output_root)
    results = apply_classification_plan([plan])

    assert results[0].status == "completed"
    assert not source.exists()
    assert (output_root / "PDF" / "보고서.pdf").read_bytes() == b"pdf"


def test_set_file_timestamps_updates_created_and_modified_times():
    workdir = case_dir("timestamps-set")
    source = workdir / "report.pdf"
    source.write_bytes(b"pdf")
    created = datetime(2024, 1, 2, 3, 4, 5).timestamp()
    modified = datetime(2024, 2, 3, 4, 5, 6).timestamp()

    set_file_timestamps(source, created=created, modified=modified)
    timestamps = get_file_timestamps(source)

    assert abs(timestamps.created - created) < 2
    assert abs(timestamps.modified - modified) < 2


def test_date_change_plan_apply_and_undo_restores_original_times():
    workdir = case_dir("date-change-undo")
    source = workdir / "20260427_report.pdf"
    source.write_bytes(b"pdf")
    original_created = datetime(2023, 1, 1, 9, 0, 0).timestamp()
    original_modified = datetime(2023, 1, 2, 9, 0, 0).timestamp()
    set_file_timestamps(source, created=original_created, modified=original_modified)
    new_created = datetime(2025, 5, 6, 7, 8, 9).timestamp()
    new_modified = datetime(2025, 6, 7, 8, 9, 10).timestamp()

    [plan] = build_date_change_plan(
        [source],
        created_timestamp=new_created,
        modified_timestamp=new_modified,
    )
    results = apply_date_change_plan([plan])

    changed = get_file_timestamps(source)
    assert results[0].status == "completed"
    assert abs(changed.created - new_created) < 2
    assert abs(changed.modified - new_modified) < 2

    undo_results = undo_date_change_results(results)

    restored = get_file_timestamps(source)
    assert undo_results[0].status == "undone"
    assert abs(restored.created - original_created) < 2
    assert abs(restored.modified - original_modified) < 2


def test_date_change_plan_can_use_date_from_file_name():
    workdir = case_dir("date-change-filename")
    source = workdir / "회의록_20260427.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_date_change_plan(
        [source],
        from_filename=True,
        change_created=True,
        change_modified=True,
    )

    expected = datetime(2026, 4, 27, 0, 0, 0).timestamp()
    assert plan.status == "ready"
    assert abs(plan.target_timestamps.created - expected) < 2
    assert abs(plan.target_timestamps.modified - expected) < 2


def test_undo_rename_results_restores_completed_renames_without_overwrite():
    workdir = case_dir("undo-rename")
    source = workdir / "report.pdf"
    source.write_bytes(b"pdf")
    [plan] = build_rename_plan([source], RenameOptions(suffix="_done"))
    results = apply_rename_plan([plan])

    undo_results = undo_rename_results(results)

    assert undo_results[0].status == "undone"
    assert source.read_bytes() == b"pdf"
    assert not (workdir / "report_done.pdf").exists()

    source.write_bytes(b"occupied")
    retry_results = undo_rename_results(results)

    assert retry_results[0].status == "failed"
    assert source.read_bytes() == b"occupied"


def test_undo_classification_results_restores_completed_moves_without_overwrite():
    workdir = case_dir("undo-classification")
    source = workdir / "report.pdf"
    output_root = workdir / "sorted"
    source.write_bytes(b"pdf")
    [plan] = build_classification_plan([source], output_root)
    results = apply_classification_plan([plan])

    undo_results = undo_classification_results(results)

    assert undo_results[0].status == "undone"
    assert source.read_bytes() == b"pdf"
    assert not (output_root / "PDF" / "report.pdf").exists()

    source.write_bytes(b"occupied")
    retry_results = undo_classification_results(results)

    assert retry_results[0].status == "failed"
    assert source.read_bytes() == b"occupied"
