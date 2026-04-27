from pathlib import Path

from file_compressor.discovery import discover_supported_files
from file_compressor.engine import expand_sources


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_discover_supported_files_recurses_and_filters_unsupported():
    source_root = case_dir("discovery-recursive") / "docs"
    nested = source_root / "quarterly" / "april"
    nested.mkdir(parents=True, exist_ok=True)

    supported_top = source_root / "budget.xlsx"
    supported_nested = nested / "slides.PDF"
    supported_deep = source_root / "quarterly" / "summary.hwpx"
    unsupported = nested / "notes.txt"
    unsupported_image = source_root / "diagram.png"

    supported_top.write_text("xlsx")
    supported_nested.write_text("pdf")
    supported_deep.write_text("hwpx")
    unsupported.write_text("ignore")
    unsupported_image.write_text("ignore")

    assert discover_supported_files(source_root) == [
        supported_top,
        supported_nested,
        supported_deep,
    ]


def test_expand_sources_returns_deterministic_supported_paths():
    workdir = case_dir("discovery-sorted")
    source_root = workdir / "batch"
    (source_root / "alpha").mkdir(parents=True, exist_ok=True)
    (source_root / "zulu").mkdir(parents=True, exist_ok=True)

    standalone = workdir / "zzz.hwp"
    first = source_root / "zulu" / "deck.ppt"
    second = source_root / "alpha" / "budget.xls"
    third = source_root / "alpha" / "overview.hwpx"
    unsupported = workdir / "aaa.txt"
    ignored_nested = source_root / "alpha" / "draft.docx"

    standalone.write_text("hwp")
    first.write_text("ppt")
    second.write_text("xls")
    third.write_text("hwpx")
    unsupported.write_text("ignore")
    ignored_nested.write_text("ignore")

    assert expand_sources([standalone, unsupported, source_root]) == [
        second,
        third,
        first,
        standalone,
    ]


def test_expand_sources_deduplicates_files_selected_directly_and_through_folder():
    workdir = case_dir("discovery-dedupe")
    source_root = workdir / "batch"
    source_root.mkdir(parents=True, exist_ok=True)
    source = source_root / "budget.xlsx"
    source.write_text("xlsx")

    assert expand_sources([source, source_root]) == [source]
