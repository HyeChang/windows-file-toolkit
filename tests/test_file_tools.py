from datetime import date
import os
from pathlib import Path
import shutil

from file_compressor.file_tools import (
    RenameOptions,
    apply_rename_plan,
    build_rename_plan,
    clean_file_stem,
    extract_date_from_name,
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
