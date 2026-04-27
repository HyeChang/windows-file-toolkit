from pathlib import Path
import shutil

from file_compressor.models import CompressionJob
from file_compressor.planning import (
    folder_batch_output_root,
    plan_folder_job,
    planned_output_folder_path,
)


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def test_folder_batch_output_root_uses_sibling_korean_suffix():
    workdir = case_dir("planning-root")
    source_root = workdir / "문서"
    source_root.mkdir()

    result = folder_batch_output_root(source_root)

    assert result == workdir / "문서_압축됨"


def test_folder_batch_output_root_avoids_existing_sibling_folder():
    workdir = case_dir("planning-root-collision")
    source_root = workdir / "문서"
    source_root.mkdir()
    (workdir / "문서_압축됨").mkdir()

    result = folder_batch_output_root(source_root)

    assert result == workdir / "문서_압축됨_2"


def test_folder_batch_output_root_avoids_existing_sibling_files():
    workdir = case_dir("planning-root-file-collision")
    source_root = workdir / "문서"
    source_root.mkdir()
    (workdir / "문서_압축됨").write_text("occupied", encoding="utf-8")
    (workdir / "문서_압축됨_2").write_text("occupied", encoding="utf-8")

    result = folder_batch_output_root(source_root)

    assert result == workdir / "문서_압축됨_3"


def test_plan_folder_job_preserves_relative_path_under_batch_root():
    workdir = case_dir("planning-relative-path")
    source_root = workdir / "docs"
    source = source_root / "nested" / "report.pdf"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"pdf")

    job = plan_folder_job(source, source_root)

    assert job == CompressionJob(
        source=source,
        output=workdir / "docs_압축됨" / "nested" / "report.pdf",
        batch_root=workdir / "docs_압축됨",
    )


def test_plan_folder_job_converts_legacy_office_output_suffixes():
    workdir = case_dir("planning-legacy-suffixes")
    source_root = workdir / "docs"
    source_root.mkdir()

    xls_job = plan_folder_job(source_root / "budget.xls", source_root)
    ppt_job = plan_folder_job(source_root / "deck.ppt", source_root)

    assert xls_job.output == workdir / "docs_압축됨" / "budget.xlsx"
    assert ppt_job.output == workdir / "docs_압축됨" / "deck.pptx"


def test_plan_folder_job_keeps_hwp_output_suffix():
    workdir = case_dir("planning-hwp-suffix")
    source_root = workdir / "docs"
    source_root.mkdir()

    job = plan_folder_job(source_root / "draft.hwp", source_root)

    assert job.output == workdir / "docs_압축됨" / "draft.hwp"


def test_planned_output_folder_path_uses_compressed_name_for_single_files():
    workdir = case_dir("planning-output-folder-file")
    output_root = workdir / "out"
    source = workdir / "docs" / "report.pdf"

    result = planned_output_folder_path(source, output_root)

    assert result == output_root / "report_compressed.pdf"


def test_planned_output_folder_path_converts_legacy_single_file_suffix():
    workdir = case_dir("planning-output-folder-legacy-file")
    output_root = workdir / "out"
    source = workdir / "docs" / "budget.xls"

    result = planned_output_folder_path(source, output_root)

    assert result == output_root / "budget_compressed.xlsx"


def test_planned_output_folder_path_preserves_folder_relative_path():
    workdir = case_dir("planning-output-folder-relative")
    source_root = workdir / "docs"
    output_root = workdir / "out"
    source = source_root / "nested" / "deck.ppt"

    result = planned_output_folder_path(source, output_root, source_root=source_root)

    assert result == output_root / "nested" / "deck.pptx"
