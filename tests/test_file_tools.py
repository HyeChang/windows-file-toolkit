from datetime import date, datetime
import os
from pathlib import Path
import shutil

from file_compressor.file_tools import (
    _NAME_SIMILARITY_THRESHOLDS,
    _existing_folder_threshold,
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
    assert extract_date_from_name("22년9월 급여명세서.pdf") == date(2022, 9, 1)
    assert extract_date_from_name("2022년 9월 급여명세서.pdf") == date(2022, 9, 1)
    assert extract_date_from_name("2025-01-09 14 26 21.png") == date(2025, 1, 9)
    assert extract_date_from_name("20250109142621.png") == date(2025, 1, 9)
    assert extract_date_from_name("20250109 1426 보고서.png") == date(2025, 1, 9)
    assert extract_date_from_name("backup_2024년_7월_18일_오후_8-27-43.zip") == date(2024, 7, 18)


def test_rename_plan_normalizes_date_to_file_name_suffix_compact():
    workdir = case_dir("rename-date-suffix-compact")
    source = workdir / "2026.04.27_회의록 초안.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_rename_plan([source], RenameOptions(date_format="suffix_compact"))

    assert plan.status == "ready"
    assert plan.target == workdir / "회의록 초안_20260427.pdf"


def test_rename_plan_normalizes_date_to_file_name_suffix_short_compact():
    workdir = case_dir("rename-date-suffix-short-compact")
    source = workdir / "2026.04.27_회의록 초안.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_rename_plan([source], RenameOptions(date_format="suffix_short_compact"))

    assert plan.status == "ready"
    assert plan.target == workdir / "회의록 초안_260427.pdf"


def test_rename_plan_normalizes_date_to_file_name_prefix_short_compact():
    workdir = case_dir("rename-date-prefix-short-compact")
    source = workdir / "2026.04.27_회의록 초안.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_rename_plan([source], RenameOptions(date_format="prefix_short_compact"))

    assert plan.status == "ready"
    assert plan.target == workdir / "260427_회의록 초안.pdf"


def test_rename_plan_normalizes_year_month_to_prefix_underscore():
    workdir = case_dir("rename-year-month-prefix-underscore")
    source = workdir / "22년9월 급여명세서.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_rename_plan([source], RenameOptions(date_format="prefix_underscore"))

    assert plan.status == "ready"
    assert plan.target == workdir / "2022_09_급여명세서.pdf"


def test_rename_plan_keeps_day_for_prefix_underscore_when_day_exists():
    workdir = case_dir("rename-full-date-prefix-underscore")
    source = workdir / "2022년 9월 7일 급여명세서.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_rename_plan([source], RenameOptions(date_format="prefix_underscore"))

    assert plan.status == "ready"
    assert plan.target == workdir / "2022_09_07_급여명세서.pdf"


def test_rename_plan_ignores_time_suffix_when_normalizing_date():
    workdir = case_dir("rename-date-time-prefix-underscore")
    cases = {
        "2025-01-09 14 26 21.png": "2025_01_09.png",
        "20250110142621.png": "2025_01_10.png",
        "2025-01-09 142621 보고서.png": "2025_01_09_보고서.png",
        "20250110 1426 보고서.png": "2025_01_10_보고서.png",
    }
    sources = []
    for name in cases:
        source = workdir / name
        source.write_bytes(b"image")
        sources.append(source)

    plans = build_rename_plan(sources, RenameOptions(date_format="prefix_underscore"))

    assert [plan.status for plan in plans] == ["ready"] * len(sources)
    assert [plan.target.name for plan in plans] == list(cases.values())


def test_rename_plan_normalizes_month_day_without_year_to_prefix_underscore():
    workdir = case_dir("rename-month-day-prefix-underscore")
    first = workdir / "★7 SF-TD4 프로그램설계서 양식_V1.0(1219).hwp"
    second = workdir / "(태양세탁기계)솔루션 기능 구성도(0930)초안.hwp"
    first.write_bytes(b"hwp")
    second.write_bytes(b"hwp")

    plans = build_rename_plan([first, second], RenameOptions(date_format="prefix_underscore"))

    assert [plan.status for plan in plans] == ["ready", "ready"]
    assert plans[0].target.name == "12_19_★7 SF-TD4 프로그램설계서 양식_V1.0.hwp"
    assert plans[1].target.name == "09_30_(태양세탁기계)솔루션 기능 구성도초안.hwp"


def test_rename_plan_does_not_treat_version_number_as_month_day_date():
    workdir = case_dir("rename-version-number-not-date")
    cases = [
        "하멜 MES DB 명세서 Ver.1.08.xlsx",
        "하멜 MES DB 명세서 v1.08.xlsx",
        "하멜 MES DB 명세서 Version_1.08.xlsx",
        "하멜 MES DB 명세서 버전 1.08.xlsx",
    ]
    sources = []
    for name in cases:
        source = workdir / name
        source.write_bytes(b"xlsx")
        sources.append(source)

    plans = build_rename_plan(sources, RenameOptions(date_format="suffix_compact"))

    assert [plan.status for plan in plans] == ["unchanged"] * len(cases)
    assert [plan.target.name for plan in plans] == cases
    assert extract_date_from_name("하멜 MES DB 명세서 Ver.1.08.xlsx") is None


def test_rename_plan_normalizes_korean_ampm_backup_datetime():
    workdir = case_dir("rename-korean-ampm-backup-datetime")
    source = workdir / "backup_2024년_7월_18일_오후_8-27-43.zip"
    source.write_bytes(b"zip")

    [plan] = build_rename_plan([source], RenameOptions(date_format="prefix_underscore"))

    assert plan.status == "ready"
    assert plan.target.name == "2024_07_18_backup.zip"


def test_rename_plan_uses_modified_date_when_name_has_no_date():
    workdir = case_dir("rename-fallback-modified-date")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")
    modified = datetime(2024, 7, 18, 9, 10, 11).timestamp()
    os.utime(source, (modified, modified))

    [plan] = build_rename_plan(
        [source],
        RenameOptions(date_format="prefix_underscore", date_fallback_source="modified"),
    )

    assert plan.status == "ready"
    assert plan.target.name == "2024_07_18_보고서.pdf"


def test_rename_plan_uses_created_date_when_name_has_no_date():
    workdir = case_dir("rename-fallback-created-date")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")
    created = datetime(2023, 12, 5, 9, 10, 11).timestamp()
    modified = datetime(2024, 7, 18, 9, 10, 11).timestamp()
    set_file_timestamps(source, created=created, modified=modified)

    [plan] = build_rename_plan(
        [source],
        RenameOptions(date_format="prefix_underscore", date_fallback_source="created"),
    )

    assert plan.status == "ready"
    assert plan.target.name == "2023_12_05_보고서.pdf"


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


def test_classification_plan_can_group_by_similar_file_names_across_extensions():
    workdir = case_dir("classification-name-similarity")
    output_root = workdir / "sorted"
    quote_pdf = workdir / "2026_견적서_ABC.pdf"
    quote_xlsx = workdir / "ABC 견적서 최종.xlsx"
    meeting_docx = workdir / "회의록_2026-05-01.docx"
    meeting_pdf = workdir / "회의록 2026.05.02.pdf"
    for source in (quote_pdf, quote_xlsx, meeting_docx, meeting_pdf):
        source.write_bytes(b"file")

    plans = build_classification_plan(
        [quote_pdf, quote_xlsx, meeting_docx, meeting_pdf],
        output_root,
        strategy="name_similarity",
        sensitivity="normal",
    )

    assert plans[0].category == plans[1].category
    assert plans[2].category == plans[3].category
    assert plans[0].category != plans[2].category
    assert plans[0].target.parent == plans[1].target.parent
    assert plans[2].target.parent == plans[3].target.parent
    assert plans[1].target.parent.name not in {"Excel", "Documents"}


def test_classification_plan_supports_five_similarity_sensitivity_levels():
    assert _NAME_SIMILARITY_THRESHOLDS == {
        "loose": 0.25,
        "medium_loose": 0.35,
        "normal": 0.45,
        "medium_strict": 0.60,
        "strict": 0.75,
    }
    assert [_existing_folder_threshold(level) for level in _NAME_SIMILARITY_THRESHOLDS] == [
        0.30,
        0.375,
        0.45,
        0.55,
        0.65,
    ]


def test_classification_plan_medium_loose_groups_between_loose_and_normal():
    workdir = case_dir("classification-name-similarity-medium-loose")
    output_root = workdir / "sorted"
    first = workdir / "가 나 하나둘셋넷다섯.pdf"
    second = workdir / "가 나 여섯일곱여덟 아홉열.xlsx"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    normal_plans = build_classification_plan(
        [first, second],
        output_root,
        strategy="name_similarity",
        sensitivity="normal",
    )
    medium_loose_plans = build_classification_plan(
        [first, second],
        output_root,
        strategy="name_similarity",
        sensitivity="medium_loose",
    )

    assert normal_plans[0].category != normal_plans[1].category
    assert medium_loose_plans[0].category == medium_loose_plans[1].category


def test_classification_plan_can_skip_category_folder_for_single_file():
    workdir = case_dir("classification-single-file-no-folder")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_classification_plan(
        [source],
        output_root,
        skip_single_file_category_folder=True,
    )

    assert plan.category == "PDF"
    assert plan.status == "ready"
    assert plan.target == output_root / "보고서.pdf"


def test_classification_plan_keeps_category_folder_for_single_file_when_disabled():
    workdir = case_dir("classification-single-file-folder-enabled")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    [plan] = build_classification_plan(
        [source],
        output_root,
        skip_single_file_category_folder=False,
    )

    assert plan.target == output_root / "PDF" / "보고서.pdf"


def test_classification_plan_single_file_skip_overrides_existing_similar_folder():
    workdir = case_dir("classification-single-file-skip-existing-folder")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    existing_category_folder = output_root / "PDF"
    existing_category_folder.mkdir(parents=True)
    source.write_bytes(b"pdf")

    [plan] = build_classification_plan(
        [source],
        output_root,
        operation="copy",
        prefer_existing_similar_folders=True,
        skip_single_file_category_folder=True,
    )

    assert plan.status == "ready"
    assert plan.target == output_root / "보고서.pdf"
    assert plan.target.parent != existing_category_folder


def test_classification_plan_prefers_existing_similar_output_folder():
    workdir = case_dir("classification-existing-similar-folder")
    output_root = workdir / "sorted"
    existing_folder = output_root / "유니투스 회의 파일"
    existing_folder.mkdir(parents=True)
    meeting_txt = workdir / "시간별 회의결과.txt"
    kickoff_pptx = workdir / "유니투스(주)킥오프 화상(0429).pptx"
    meeting_txt.write_bytes(b"meeting")
    kickoff_pptx.write_bytes(b"deck")

    plans = build_classification_plan(
        [meeting_txt, kickoff_pptx],
        output_root,
        strategy="name_similarity",
        sensitivity="normal",
        prefer_existing_similar_folders=True,
    )

    assert plans[0].target == existing_folder / "시간별 회의결과.txt"
    assert plans[1].target == existing_folder / "유니투스(주)킥오프 화상(0429).pptx"
    assert plans[0].category == "유니투스 회의 파일"
    assert plans[1].category == "유니투스 회의 파일"


def test_classification_plan_prefers_distinctive_existing_folder_terms():
    workdir = case_dir("classification-existing-folder-distinctive-terms")
    output_root = workdir / "sorted"
    for folder_name in (
        "유니투스천안 일상점검 전산화 대상 문서",
        "MODULE 기능형 MES 일상점검 CHECK SHEET",
        "김천 위미르 전달 파일",
        "김천 전산화 적용 요소 정리",
        "김천공장 추가자료",
        "삼성 MDM knox정리",
        "오류 정리 문서",
        "유니투스 프로젝트 일정",
        "유니투스천안 일상점검 전산화 관련 자료 공정레이아웃",
    ):
        (output_root / folder_name).mkdir(parents=True)
    source = workdir / "유니투스 프로토타입 오류 정리 문서_Ver.260513.pptx"
    source.write_bytes(b"deck")

    [plan] = build_classification_plan(
        [source],
        output_root,
        strategy="name_similarity",
        sensitivity="normal",
        prefer_existing_similar_folders=True,
    )

    assert plan.status == "ready"
    assert plan.category == "오류 정리 문서"
    assert plan.target == output_root / "오류 정리 문서" / source.name


def test_classification_plan_requires_choice_for_ambiguous_existing_folders():
    workdir = case_dir("classification-existing-folder-ambiguous")
    output_root = workdir / "sorted"
    left = output_root / "오류 정리 문서"
    right = output_root / "오류 정리 자료"
    left.mkdir(parents=True)
    right.mkdir()
    source = workdir / "프로토타입 오류 정리_Ver.260513.pptx"
    source.write_bytes(b"deck")

    [plan] = build_classification_plan(
        [source],
        output_root,
        strategy="name_similarity",
        sensitivity="normal",
        prefer_existing_similar_folders=True,
    )

    assert plan.status == "needs_choice"
    assert plan.target == output_root / "프로토타입 오류 정리" / source.name
    assert [candidate.path for candidate in plan.folder_candidates] == [left, right]
    assert [candidate.matched_terms for candidate in plan.folder_candidates] == [
        ("오류", "정리"),
        ("오류", "정리"),
    ]


def test_classification_plan_ignores_existing_similar_output_folder_when_disabled():
    workdir = case_dir("classification-existing-similar-folder-disabled")
    output_root = workdir / "sorted"
    existing_folder = output_root / "유니투스 회의 파일"
    existing_folder.mkdir(parents=True)
    source = workdir / "유니투스(주)킥오프 화상(0429).pptx"
    source.write_bytes(b"deck")

    [plan] = build_classification_plan(
        [source],
        output_root,
        strategy="name_similarity",
        sensitivity="normal",
        prefer_existing_similar_folders=False,
    )

    assert plan.target.parent != existing_folder


def test_classification_plan_uses_unique_organized_folder_when_output_root_missing():
    workdir = case_dir("classification-auto-output")
    source_pdf = workdir / "보고서.pdf"
    source_xlsx = workdir / "예산.xlsx"
    source_pdf.write_bytes(b"pdf")
    source_xlsx.write_bytes(b"xlsx")
    (workdir / "정리").mkdir()
    (workdir / "정리_1").mkdir()

    plans = build_classification_plan([source_pdf, source_xlsx], None)

    assert plans[0].target == workdir / "정리_2" / "PDF" / "보고서.pdf"
    assert plans[1].target == workdir / "정리_2" / "Excel" / "예산.xlsx"


def test_classification_plan_marks_existing_identical_target_as_duplicate():
    workdir = case_dir("classification-duplicate-existing")
    source = workdir / "보고서.pdf"
    output_root = workdir / "sorted"
    target = output_root / "PDF" / "보고서.pdf"
    target.parent.mkdir(parents=True)
    source.write_bytes(b"same")
    target.write_bytes(b"same")

    [plan] = build_classification_plan([source], output_root)
    results = apply_classification_plan([plan])

    assert plan.status == "duplicate"
    assert plan.target == target
    assert source.read_bytes() == b"same"
    assert target.read_bytes() == b"same"
    assert not (output_root / "PDF" / "보고서_2.pdf").exists()
    assert results[0].status == "duplicate"


def test_classification_plan_can_delete_existing_identical_duplicate_source():
    workdir = case_dir("classification-duplicate-delete")
    source = workdir / "보고서.pdf"
    output_root = workdir / "sorted"
    target = output_root / "PDF" / "보고서.pdf"
    target.parent.mkdir(parents=True)
    source.write_bytes(b"same")
    target.write_bytes(b"same")

    [plan] = build_classification_plan([source], output_root, duplicate_action="delete")
    results = apply_classification_plan([plan])

    assert plan.status == "duplicate"
    assert plan.duplicate_action == "delete"
    assert results[0].status == "duplicate_deleted"
    assert not source.exists()
    assert target.read_bytes() == b"same"
    assert not (output_root / "PDF" / "보고서_2.pdf").exists()


def test_classification_plan_keeps_conflicting_name_when_content_differs():
    workdir = case_dir("classification-different-existing")
    source = workdir / "보고서.pdf"
    output_root = workdir / "sorted"
    existing = output_root / "PDF" / "보고서.pdf"
    existing.parent.mkdir(parents=True)
    source.write_bytes(b"new")
    existing.write_bytes(b"old")

    [plan] = build_classification_plan([source], output_root)

    assert plan.status == "ready"
    assert plan.target == output_root / "PDF" / "보고서_2.pdf"


def test_classification_plan_uses_auto_organized_folder_per_source_parent():
    workdir = case_dir("classification-auto-output-per-folder")
    left = workdir / "left" / "보고서.pdf"
    right = workdir / "right" / "예산.xlsx"
    left.parent.mkdir()
    right.parent.mkdir()
    left.write_bytes(b"pdf")
    right.write_bytes(b"xlsx")

    plans = build_classification_plan([left, right], None)

    assert plans[0].target == left.parent / "정리" / "PDF" / "보고서.pdf"
    assert plans[1].target == right.parent / "정리" / "Excel" / "예산.xlsx"


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


def test_apply_classification_plan_copies_files_to_category_folder_without_moving_source():
    workdir = case_dir("classification-copy")
    source = workdir / "보고서.pdf"
    output_root = workdir / "sorted"
    source.write_bytes(b"pdf")

    [plan] = build_classification_plan([source], output_root, operation="copy")
    results = apply_classification_plan([plan])

    assert plan.operation == "copy"
    assert results[0].status == "completed"
    assert source.read_bytes() == b"pdf"
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


def test_undo_classification_results_removes_completed_copy_without_touching_source():
    workdir = case_dir("undo-classification-copy")
    source = workdir / "report.pdf"
    output_root = workdir / "sorted"
    source.write_bytes(b"pdf")
    [plan] = build_classification_plan([source], output_root, operation="copy")
    results = apply_classification_plan([plan])

    undo_results = undo_classification_results(results)

    assert undo_results[0].status == "undone"
    assert source.read_bytes() == b"pdf"
    assert not (output_root / "PDF" / "report.pdf").exists()
