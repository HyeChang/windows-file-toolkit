from pathlib import Path
import shutil

from pypdf import PdfReader, PdfWriter

from file_compressor.pdf_tools import (
    build_single_pdf_plan,
    delete_pages,
    default_merge_plan,
    extract_pages,
    merge_pdfs,
    parse_page_selection,
    pdf_page_refs,
    reorder_pages,
    rotate_pages,
    split_pdf,
    write_page_plan,
)


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def write_pdf(path: Path, page_count: int):
    writer = PdfWriter()
    for index in range(page_count):
        writer.add_blank_page(width=200 + index, height=300 + index)
    with path.open("wb") as output:
        writer.write(output)


def page_count(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


def page_widths(path: Path) -> list[int]:
    return [int(page.mediabox.width) for page in PdfReader(str(path)).pages]


def test_parse_page_selection_supports_ranges_and_order():
    assert parse_page_selection("1,3-5,2", total_pages=6) == [0, 2, 3, 4, 1]


def test_merge_pdfs_combines_files_without_overwriting():
    workdir = case_dir("pdf-merge")
    first = workdir / "first.pdf"
    second = workdir / "second.pdf"
    output = workdir / "merged.pdf"
    write_pdf(first, 2)
    write_pdf(second, 1)
    output.write_bytes(b"occupied")

    result = merge_pdfs([first, second], output)

    assert result.status == "completed"
    assert result.output == workdir / "merged_2.pdf"
    assert page_count(result.output) == 3
    assert output.read_bytes() == b"occupied"


def test_split_pdf_writes_one_file_per_page():
    workdir = case_dir("pdf-split")
    source = workdir / "source.pdf"
    output_dir = workdir / "pages"
    write_pdf(source, 3)

    result = split_pdf(source, output_dir)

    assert result.status == "completed"
    assert [path.name for path in result.outputs] == [
        "source_page_001.pdf",
        "source_page_002.pdf",
        "source_page_003.pdf",
    ]
    assert all(page_count(path) == 1 for path in result.outputs)


def test_extract_delete_rotate_and_reorder_pages():
    workdir = case_dir("pdf-page-ops")
    source = workdir / "source.pdf"
    write_pdf(source, 4)

    extracted = extract_pages(source, workdir / "extract.pdf", "2-3")
    deleted = delete_pages(source, workdir / "delete.pdf", "2,4")
    rotated = rotate_pages(source, workdir / "rotate.pdf", "1,3", 90)
    reordered = reorder_pages(source, workdir / "reorder.pdf", "4,2,1")

    assert page_count(extracted.output) == 2
    assert page_widths(extracted.output) == [201, 202]
    assert page_count(deleted.output) == 2
    assert page_widths(deleted.output) == [200, 202]
    assert page_count(rotated.output) == 4
    assert int(PdfReader(str(rotated.output)).pages[0].get("/Rotate")) == 90
    assert int(PdfReader(str(rotated.output)).pages[2].get("/Rotate")) == 90
    assert page_widths(reordered.output) == [203, 201, 200]


def test_pdf_page_refs_and_default_merge_plan_show_source_pages():
    workdir = case_dir("pdf-page-refs")
    first = workdir / "first.pdf"
    second = workdir / "second.pdf"
    write_pdf(first, 2)
    write_pdf(second, 1)

    refs = pdf_page_refs(first)
    plan = default_merge_plan([first, second])

    assert [(ref.source, ref.page_number, ref.result_order) for ref in refs] == [
        (first, 1, 1),
        (first, 2, 2),
    ]
    assert [(row.source.name, row.page_number, row.result_order, row.action) for row in plan] == [
        ("first.pdf", 1, 1, "include"),
        ("first.pdf", 2, 2, "include"),
        ("second.pdf", 1, 3, "include"),
    ]


def test_write_page_plan_uses_visible_plan_order():
    workdir = case_dir("pdf-write-plan")
    first = workdir / "first.pdf"
    second = workdir / "second.pdf"
    output = workdir / "merged.pdf"
    write_pdf(first, 2)
    write_pdf(second, 2)
    plan = default_merge_plan([first, second])
    visible_order = [plan[2], plan[0], plan[3]]

    result = write_page_plan(visible_order, output)

    assert result.status == "completed"
    assert page_widths(result.output) == [200, 200, 201]


def test_build_single_pdf_plan_marks_actions_and_outputs():
    workdir = case_dir("pdf-single-plan")
    source = workdir / "source.pdf"
    output = workdir / "out.pdf"
    write_pdf(source, 4)

    extract_plan = build_single_pdf_plan(source, "extract", "2,4", output)
    delete_plan = build_single_pdf_plan(source, "delete", "2", output)
    split_plan = build_single_pdf_plan(source, "split", "", workdir / "pages")
    rotate_plan = build_single_pdf_plan(source, "rotate", "1,3", output, rotation=90)
    reorder_plan = build_single_pdf_plan(source, "reorder", "4,2", output)

    assert [(row.page_number, row.action) for row in extract_plan] == [
        (1, "exclude"),
        (2, "include"),
        (3, "exclude"),
        (4, "include"),
    ]
    assert [(row.page_number, row.action) for row in delete_plan] == [
        (1, "keep"),
        (2, "delete"),
        (3, "keep"),
        (4, "keep"),
    ]
    assert [row.output.name for row in split_plan] == [
        "source_page_001.pdf",
        "source_page_002.pdf",
        "source_page_003.pdf",
        "source_page_004.pdf",
    ]
    assert [(row.page_number, row.rotation) for row in rotate_plan] == [(1, 90), (2, 0), (3, 90), (4, 0)]
    assert [(row.page_number, row.result_order, row.action) for row in reorder_plan] == [
        (4, 1, "include"),
        (2, 2, "include"),
    ]
